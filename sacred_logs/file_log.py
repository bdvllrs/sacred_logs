import datetime
import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def update_source_path_prefix(base_dir, paths):
    """
    Tries to match the sources and updates the files
    Args:
        base_dir: source to replace
        paths: list of paths
    """
    path_steps = paths[0][0].split('/')
    path_root = None
    for path_level in range(len(path_steps)):
        path_root = '/'.join(path_steps[:path_level])
        failed = False
        for path in paths:
            new_path = base_dir + path[0][len(path_root):]
            if not Path(new_path).exists():
                failed = True
                break
        if not failed:
            break
    else:
        raise ValueError("The source path root is incorrect.")
    return list(map(lambda x: [x[0].replace(path_root + '/', ''), x[1]], paths))


class FileLog:
    def __init__(self, path: str):
        self.path = Path(path)

        assert self.path.exists(), f"The path {path} does not exist."

        self.config_path = self.path / "config.json"
        assert self.config_path.exists(), "config.json file missing."
        self.cout_path = self.path / "cout.txt"
        assert self.cout_path.exists(), "cout.txt file missing."
        self.metrics_path = self.path / "metrics.json"
        assert self.metrics_path.exists(), "metrics.json file missing."
        self.run_path = self.path / "run.json"
        assert self.run_path.exists(), "run.json file missing."

        with open(self.cout_path, "r") as cout_file:
            self.cout = cout_file.read()
        with open(self.config_path, 'r') as config_file:
            self.config = json.load(config_file)
        with open(self.run_path, 'r') as run_file:
            self.run = json.load(run_file)
        with open(self.metrics_path, 'r') as metrics_file:
            self.metrics = json.load(metrics_file)

    def get_metric(self, name, running_mean=None):
        """
        Get a metric and perform operation on them
        Args:
            name: name of the metric value
            running_mean: sliding window size for a running mean.
        """
        metric = self.metrics[name]
        if running_mean is not None:
            roll = pd.Series(metric['values']).rolling(running_mean)
            metric['values'] = roll.mean().values
            metric['std'] = roll.std().values
        return metric

    def plot(self, name, ax=None, x_axis="steps", log_scale=False, **kwargs):
        """
        Get plot for particular metric.
        Args:
            name: Name of metric
            ax: matplotlib ax to plot on. Default plt.gca()
            x_axis: x_axis to use. Default "steps". Can be "steps" or "timestamps".
            log_scale: if True, uses semilogy
            **kwargs: FileLog.get_metric arguments
        Returns: ax
        """
        assert x_axis in ['steps', 'timestamps'], "x_axis is incorrect."
        metric = self.get_metric(name, **kwargs)
        if ax is None:
            ax = plt.gca()
        if log_scale:
            ax.semilogy(metric[x_axis], metric['values'])
        else:
            ax.plot(metric[x_axis], metric['values'])
        if 'std' in metric:
            ax.fill_between(metric[x_axis], metric['values'] - metric['std'], metric['values'] + metric['std'],
                            color='blue', alpha=0.2)
        return ax

    def __getattr__(self, item):
        if item in self.run:
            return self.run[item]

    def __getitem__(self, item):
        if item in self.run:
            return self.run[item]

    def to_mongo(self, base_dir, remove_sources=False,
                 overwrite=None, *args, **kwargs):
        """
        Exports the file log into a mongo database.
        Requires sacred to be installed.
        Args:
            base_dir: root path to sources
            remove_sources: if sources are too complicated to match
            overwrite: whether to overwrite an experiment
            *args: args of the MongoObserver
            **kwargs: keyword args of the MongoObserver
        """
        from sacred.observers import MongoObserver
        from sacred.metrics_logger import ScalarMetricLogEntry, linearize_metrics

        mongo_observer = MongoObserver(*args, overwrite=overwrite, **kwargs)

        # Start simulation of run
        experiment = self.experiment.copy()
        experiment['base_dir'] = base_dir
        # FIXME
        experiment['sources'] = [] if remove_sources else update_source_path_prefix(base_dir, experiment['sources'])
        try:
            mongo_observer.started_event(
                experiment,
                self.command,
                self.host,
                datetime.datetime.fromisoformat(self.start_time),
                self.config,
                self.meta,
                _id=overwrite
            )
        except FileNotFoundError as e:
            raise FileNotFoundError("The sources are incorrect. Try fixing paths or use `remove_sources=True`."
                                    f" Original error: {e}")

        # Add artifacts
        for artifact_name in self.artifacts:
            mongo_observer.artifact_event(
                name=artifact_name,
                filename=(self.path / artifact_name)
            )

        # Add resources
        for resource in self.resources:
            mongo_observer.resource_event(resource[0])

        # Add metrics
        size_metrics = {}
        # If overwrite, get the already added metrics.
        # FIXME: issue if steps are not increasing
        if overwrite is not None:
            metrics = mongo_observer.metrics.find({"run_id": overwrite})
            for metric in metrics:
                size_metrics[metric['name']] = len(metric['steps'])

        log_metrics = []
        for metric_name, metric in self.metrics.items():
            steps = metric['steps'] if metric_name not in size_metrics else metric['steps'][size_metrics[metric_name]:]
            timestamps = metric['timestamps'] if metric_name not in size_metrics else metric['timestamps'][size_metrics[metric_name]:]
            values = metric['values'] if metric_name not in size_metrics else metric['values'][size_metrics[metric_name]:]
            for step, timestamp, value in zip(steps, timestamps, values):
                metric_log_entry = ScalarMetricLogEntry(metric_name, step,
                                                        datetime.datetime.fromisoformat(timestamp), value)
                log_metrics.append(metric_log_entry)
        mongo_observer.log_metrics(linearize_metrics(log_metrics), {})

        mongo_observer.heartbeat_event(
            info=self.info if 'info' in self.run else None,
            captured_out=self.cout,
            beat_time=datetime.datetime.fromisoformat(self.heartbeat),
            result=self.result
        )

        # End simulation
        if self.status != "RUNNING":
            stop_time = datetime.datetime.fromisoformat(self.stop_time)

            if self.status in ["COMPLETED", "RUNNING"]:  # If still running we force it as a finished experiment
                mongo_observer.completed_event(stop_time, self.result)
            elif self.status == "INTERRUPTED":
                mongo_observer.interrupted_event(stop_time, 'INTERRUPTED')
            elif self.status == "FAILED":
                mongo_observer.failed_event(stop_time, self.fail_trace)
