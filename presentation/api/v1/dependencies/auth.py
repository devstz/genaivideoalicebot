"""FastAPI dependencies for JWT authentication."""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from uuid import UUID

from sitapi.config import get_config
from sitapi.core.enums.auth import EnvironmentRestriction
from sitapi.infra.providers.auth import (
    AuthTokenClaims,
    JWTAuthTokenProvider,
    TokenValidationError,
)
from sitapi.infra.providers.cache import get_redis_cache
from sitapi.presentation.dependencies import get_uow_dependency
from sitapi.infra.postgres.uow import SQLAlchemyUnitOfWork

security = HTTPBearer()


@lru_cache(maxsize=1)
def get_auth_provider() -> JWTAuthTokenProvider:
    """
    Get a cached instance of JWTAuthTokenProvider with Redis cache for token revocation.
    
    Returns:
        JWTAuthTokenProvider instance configured with Redis cache
    """
    config = get_config().AUTH
    cache = get_redis_cache()
    return JWTAuthTokenProvider(config, cache=cache)


async def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    provider: JWTAuthTokenProvider = Depends(get_auth_provider),
) -> AuthTokenClaims:
    """
    FastAPI dependency to extract and validate JWT token from Authorization header.
    
    Args:
        request: FastAPI Request object for extracting request information
        credentials: HTTP Bearer token credentials from Authorization header
        provider: JWT auth token provider instance
        
    Returns:
        AuthTokenClaims with validated token information
        
    Raises:
        HTTPException: 401 if token is missing, invalid, or revoked
    """
    token = credentials.credentials
    
    # Collect request information for usage history
    request_info = {
        "path": str(request.url.path),
        "method": request.method,
        "client_host": request.client.host if request.client else None,
    }
    
    try:
        # validate_token works without UoW (falls back to cache for revocation check)
        claims = await provider.validate_token(token, request_info=request_info, uow=None)
        return claims
    except TokenValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc) or "Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


async def check_token_usage_limit(
    country_code: str | None = None,
    current_user: AuthTokenClaims = Depends(get_current_user),
    uow: SQLAlchemyUnitOfWork = Depends(get_uow_dependency),
) -> None:
    """
    Check if token usage limit is exceeded, handling sandbox and production separately.
    """
    if not current_user.jti:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token does not have JTI (JWT ID)",
        )
    
    # 1. Determine environment
    env_restriction = current_user.environment_restriction
    is_sandbox = False
    
    if env_restriction == EnvironmentRestriction.SANDBOX_ONLY.value:
        is_sandbox = True
    elif env_restriction == EnvironmentRestriction.PRODUCTION_ONLY.value:
        is_sandbox = False
    elif country_code:
        # If BOTH or None, determine by country
        from sitapi.core.constants.creditsafe import is_sandbox_country
        is_sandbox = is_sandbox_country(country_code)
    else:
        # Default to production if no country and no specific restriction
        is_sandbox = False

    # 2. Get limit for the determined environment
    limit = current_user.sandbox_limit if is_sandbox else current_user.usage_limit
    total_limit = current_user.total_limit
    
    if limit is None and total_limit is None:
        # No limit set for this environment, but we still want to increment usage count for tracking
        pass
    
    from uuid import UUID
    jti = UUID(current_user.jti)
    
    token = await uow.token_repo.get_by_jti(jti)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token not found in database",
        )
    
    # 3. Check if limit exceeded before incrementing
    current_count = token.sandbox_usage_count if is_sandbox else token.usage_count
    current_total = token.total_usage_count
    
    import logging
    logger = logging.getLogger(__name__)
    env_name = "SANDBOX" if is_sandbox else "PRODUCTION"
    
    logger.info(
        f"[{current_user.subject}] Attempting {env_name} usage increment: "
        f"current_count={current_count}, limit={limit}, "
        f"total_count={current_total}, total_limit={total_limit}, "
        f"country={country_code}, env_restriction={env_restriction}"
    )
    
    # Security fix C2: Atomic increment with limit check in single DB transaction
    # This prevents race condition where multiple concurrent requests could bypass the limit
    # The increment_usage/increment_sandbox_usage methods now check the limit BEFORE incrementing
    # in a single atomic UPDATE statement with WHERE clause
    if is_sandbox:
        new_count = await uow.token_repo.increment_sandbox_usage(
            jti, 
            limit=limit, 
            total_limit=total_limit
        )
    else:
        new_count = await uow.token_repo.increment_usage(
            jti, 
            limit=limit, 
            total_limit=total_limit
        )
    
    # If new_count is None, it means the limit check failed (limit would be exceeded)
    if new_count is None:
        await uow.rollback()
        # Determine which limit was exceeded for better error message
        limit_msg = f"{env_name} usage limit exceeded ({current_count}/{limit})"
        if total_limit is not None and current_total >= total_limit:
            limit_msg = f"Total usage limit exceeded ({current_total}/{total_limit})"
        elif limit is not None and current_count >= limit:
            limit_msg = f"{env_name} usage limit exceeded ({current_count}/{limit})"
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Token {limit_msg}",
        )
        
    await uow.commit()
    
    logger.info(
        f"[{current_user.subject}] {env_name} usage incremented successfully: "
        f"{new_count}/{limit or 'unlimited'}, total: {current_total + 1}/{total_limit or 'unlimited'}"
    )


def _check_country_support(country_code: str, current_user: AuthTokenClaims) -> None:
    """Internal helper to check country support."""
    if not current_user.countries:
        # No country restrictions, allow all countries
        return
    
    country_upper = country_code.upper()
    if country_upper not in current_user.countries:
        supported = ", ".join(current_user.countries)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Token does not support country '{country_code}'. Supported countries: {supported}",
        )


def check_token_country_support(country_code: str, current_user: AuthTokenClaims) -> None:
    """
    Check if country is supported by token.
    
    This is a helper function that can be called explicitly in route handlers.
    
    Args:
        country_code: ISO 3166-1 alpha-2 country code to check
        current_user: Validated token claims
        
    Raises:
        HTTPException: 403 if country is not supported
    """
    _check_country_support(country_code, current_user)


async def check_token_usage_limit_from_report_id(
    report_id: UUID,
    current_user: AuthTokenClaims = Depends(get_current_user),
    uow: SQLAlchemyUnitOfWork = Depends(get_uow_dependency),
) -> None:
    """
    Check token usage limit using country from report.
    
    Args:
        report_id: Report ID to get country from
        current_user: Validated token claims
        uow: Database unit of work
    
    Raises:
        HTTPException: 403 if usage limit exceeded, 404 if report not found
    """
    report = await uow.company_report_repo.get(report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report {report_id} not found",
        )
    
    # Check usage limit with country from report
    await check_token_usage_limit(
        country_code=report.company_country,
        current_user=current_user,
        uow=uow,
    )


async def check_token_country_from_report_id(
    report_id: UUID,
    current_user: AuthTokenClaims = Depends(get_current_user),
    uow: SQLAlchemyUnitOfWork = Depends(get_uow_dependency),
) -> None:
    """
    Check if country from report is supported by token.
    
    Args:
        report_id: Report ID to get country from
        current_user: Validated token claims
        uow: Database unit of work
    
    Raises:
        HTTPException: 403 if country is not supported, 404 if report not found
    """
    report = await uow.company_report_repo.get(report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report {report_id} not found",
        )
    
    country_code = report.company_country
    
    # Use new environment determination logic which includes country list validation
    from sitapi.presentation.api.v1.routers.agents.report import (
        _validate_token_country_configuration,
        _determine_environment_for_country,
    )
    
    logger = logging.getLogger(__name__)
    
    try:
        # Validate token configuration
        _validate_token_country_configuration(current_user)
        
        # Determine environment - this will raise HTTPException if country is not supported
        _determine_environment_for_country(country_code, current_user)
    except HTTPException:
        # Re-raise HTTPException from validation/determination
        raise
    except Exception as e:
        # Unexpected error - log and raise generic error
        logger.error(
            f"Error checking token country support: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validating country support: {str(e)}",
        )


async def check_readonly_restrictions(
    request: Request,
    current_user: AuthTokenClaims = Depends(get_current_user),
) -> None:
    """
    Check if readonly restrictions are violated.
    
    If token has no write scopes, block all write operations (POST, PUT, DELETE, PATCH).
    Only allow read operations (GET, HEAD, OPTIONS).
    """
    # If the token has any write scope, allow write operations
    has_write_scope = any(
        ":write" in scope or "*" in scope 
        for scope in current_user.scopes
    )
    
    if not has_write_scope:
        if request.method.upper() in ("POST", "PUT", "DELETE", "PATCH"):
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(
                f"[{current_user.subject}] Readonly token (no write scopes) attempted {request.method} operation on {request.url.path}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This token does not have write permissions. Write operations (POST, PUT, DELETE, PATCH) are not allowed.",
            )



def require_scope(scope: str):
    """
    Create a dependency that requires a specific scope.
    
    Args:
        scope: Required scope string
    
    Returns:
        Dependency function that checks for the scope
    """
    async def _check_scope(
        current_user: AuthTokenClaims = Depends(get_current_user),
    ) -> None:
        """
        Check if token has the required scope.
        
        Args:
            current_user: Validated token claims
        
        Raises:
            HTTPException: 403 if scope is not present
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # If no scopes specified in token, allow access (backward compatibility)
        if not current_user.scopes:
            logger.info(
                f"[{current_user.subject}] No scopes specified in token, allowing access (backward compatibility)"
            )
            return
        
        if scope not in current_user.scopes:
            logger.warning(
                f"[{current_user.subject}] Scope check failed. Required: {scope}, "
                f"Available: {current_user.scopes}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required scope '{scope}' is not present in token. Available scopes: {', '.join(current_user.scopes)}",
            )
        
        logger.info(
            f"[{current_user.subject}] Scope check passed: {scope}"
        )
    
    return _check_scope


# Predefined scope dependencies
require_reports_read_scope = require_scope("reports:read")
require_reports_write_scope = require_scope("reports:write")
require_reports_delete_scope = require_scope("reports:delete")
require_extend_read_scope = require_scope("extend:read")
require_extend_write_scope = require_scope("extend:write")
require_admin_read_scope = require_scope("admin:read")
require_admin_write_scope = require_scope("admin:write")
require_tokens_read_scope = require_scope("tokens:read")
require_tokens_write_scope = require_scope("tokens:write")

