import matplotlib.pyplot as plt
import os

from sacred_logs import FileLog


if __name__ == "__main__":
    # Load a log
    log = FileLog("/path/to/file/log/folder")
    # Save if to a mongo database
    log.to_mongo(base_dir=os.getcwd(),
                 # overwrite=1,  # to overwrite a specific experiment
                 url="127.0.0.1:27017",
                 db_name="mongodb_name")

    # Or directly work with it...
    # Config used
    config = log.config
    # Logged outputs
    cout = log.cout
    # Information on the run
    run_info = log.run
    # You can also use log[run_item] or log.run_item instead of log.run[run_item]
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
