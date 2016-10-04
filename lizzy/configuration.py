import environmental


class Configuration:  # pylint: disable=too-few-public-methods
    """
    Configuration parameters to be fetched from the environment
    """
    allowed_users = environmental.List('ALLOWED_USERS', None)
    allowed_user_pattern = environmental.Str('ALLOWED_USER_PATTERN', None)  # Username pattern
    deployer_scope = environmental.Str('DEPLOYER_SCOPE')  # OAUTH scope needed to deploy
    log_level = environmental.Str('LOG_LEVEL', 'INFO')
    log_format = environmental.Str('LOG_FORMAT', 'default')
    region = environmental.Str('REGION', 'eu-west-1')  # AWS Region
    token_url = environmental.Str('TOKEN_URL')
    token_info_url = environmental.Str('TOKENINFO_URL')
    kairosdb_url = environmental.Str('KAIROSDB_URL', None)
    metrics_prefix = environmental.Str('METRICS_PREFIX', 'default')
    sentry_dsn = environmental.Str('SENTRY_DSN', None)


config = Configuration()  # pylint: disable=invalid-name
