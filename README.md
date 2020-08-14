# SacredLogs
Manages file logs in sacred.
- Get run, metrics and config information
- Plot metrics easily
- Export to a mongo database (as if a MongoObserver were used)

## Install
`pip install https://github.com/bdvllrs/sacred_logs.git`

## Issues
- Sources when exporting to mongo in certain cases.
- Metrics when overwrite an experiment.

## Quickstart

### Cli
```
sacredlogs export [OPTIONS] OBSERVER PATH DB_NAME
```
- `OBSERVER`: What observer to export to (mongo or neptune)
- `PATH`: path to the file log folder
- `DB_NAME`: name of the mongo database or neptune project name to export to.

#### Options
- `--token`, `-t`: Neptune API token.
- `--basedir`, `-b`: base directory for the sources. Defaults to current folder.
- `--url`, `-u`: mongo db server url. Defaults to "127.0.0.1:27017"
- `--overwrite`, `-o`: id of the experiment to overwrite.
- `--skip_sources`, `-s`: skip importing sources in the mongo database.

#### Examples:
```
sacredlogs export mongo /path/to/file/log my_mongo_db
```

```
sacredlogs export neptune /path/to/file/log USER_NAME/PROJECT_NAME --token=YOUR_API_TOKEN
```

### Code

```python
import matplotlib.pyplot as plt
from sacred_logs import FileLog


# Load a log
log = FileLog("/path/to/file/log/folder")
# Save if to a mongo database
log.to_mongo(base_dir="/path/to/project/source",
             # overwrite=1,  # to overwrite a specific experiment
             url="127.0.0.1:27017",
             db_name="db_name")

# Or directly work with it...
# Config used
config = log.config
# Logged outputs
cout = log.cout
# Information on the run
run_info = log.run
# You can also use log[run_item] instead of log.run[run_item]
seed = log.seed
# Get metrics
train_acc = log.get_metric('train_acc',
                           running_mean=10)  # With a running mean of 10
steps = train_acc['steps']
values = train_acc['values']
std = train_acc['std']  # only exists because of the running mean
timestamps = train_acc['timestamps']
# Plot
log.plot("train_acc", x_axis="steps", running_mean=10)
plt.show()
```