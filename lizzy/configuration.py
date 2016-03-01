import environmental


class Configuration:
    """
    Configuration parameters to be fetched from the environment
    """
    allowed_users = environmental.List('ALLOWED_USERS', None)
    deployer_scope = environmental.Str('DEPLOYER_SCOPE')  # OAUTH scope needed to deploy
    job_interval = environmental.Int('JOB_INTERVAL', 15)  # how many seconds to wait between job runs
    log_level = environmental.Str('LOG_LEVEL', 'INFO')
    log_format = environmental.Str('LOG_FORMAT', 'default')
    redis_host = environmental.Str('REDIS_HOST', 'localhost')
    redis_port = environmental.Int('REDIS_PORT', 6379)
    region = environmental.Str('REGION', 'eu-west-1')  # AWS Region
    token_url = environmental.Str('TOKEN_URL')
    token_info_url = environmental.Str('TOKENINFO_URL')


config = Configuration()
