
# The folder of database
DATABASE_NAME = "server_cache.db"

# The mean value of DeepLab model
IMG_MEAN = (104.00698793, 116.66876762, 122.67891434)

# The shape of image used for FST
IMG_SHAPE = (236, 420, 3)

# The time interval between two retries when NFD is down
DISCONN_RETRY_TIME = 2.0

# The prefix of application
SERVER_PREFIX = "icear-server"

# The prefix for calculation commands
COMMAND_PREFIX = "calc"

# The prefix for fetching results
RESULT_PREFIX = "result"

# The "prefix" of status sets.
# Only used by database. Invisible to remote consumer.
STATUS_PREFIX = "status"

# The model file of DeepLab
DEEPLAB_MODEL_PATH = "deeplab_resnet.ckpt"

# The folder of model files for FST
FST_MODEL_PATH = "ce-models"

# Max number of attempts
FETCHER_MAX_ATTEMPT_NUMBER = 3

# Milliseconds between two trial
FETCHER_RETRY_INTERVAL = 1000.0

# Refuse too large data
FETCHER_FINAL_BLOCK_ID = 100

# Max number of interest packets in flight
FETCHER_MAX_INTEREST_IN_FLIGHT = 10
