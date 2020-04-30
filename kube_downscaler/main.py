#!/usr/bin/env python3
import logging
import time
import os

from kube_downscaler import __version__
from kube_downscaler import cmd
from kube_downscaler import shutdown
from kube_downscaler.scaler import scale

logger = logging.getLogger("downscaler")


def main(args=None):
    parser = cmd.get_parser()
    args = parser.parse_args(args)

    logging.basicConfig(
        format="%(asctime)s %(levelname)s: %(message)s",
        level=logging.DEBUG if args.debug else logging.INFO,
    )

    config_str = ", ".join(f"{k}={v}" for k, v in sorted(vars(args).items()))
    logger.info(f"Downscaler v{__version__} started with {config_str}")

    if args.dry_run:
        logger.info("**DRY-RUN**: no downscaling will be performed!")

    return run_loop(
        args.once,
        args.namespace,
        args.include_resources,
        args.upscale_period,
        args.downscale_period,
        args.default_uptime,
        args.default_downtime,
        args.exclude_namespaces,
        args.exclude_deployments,
        args.grace_period,
        args.interval,
        args.dry_run,
        args.downtime_replicas,
        args.deployment_time_annotation,
    )


def run_loop(
    run_once,
    namespace,
    include_resources,
    upscale_period,
    downscale_period,
    default_uptime,
    default_downtime,
    exclude_namespaces,
    exclude_deployments,
    grace_period,
    interval,
    dry_run,
    downtime_replicas,
    deployment_time_annotation=None,
):
    handler = shutdown.GracefulShutdown()
    while True:
        if os.path.exists("/config/EXCLUDE_NAMESPACES"):
            exclude_namespaces=open("/config/EXCLUDE_NAMESPACES").read()
        if os.path.exists("/config/DEFAULT_UPTIME"):
            default_uptime=open("/config/DEFAULT_UPTIME").read()
        if os.path.exists("/config/DEFAULT_DOWNTIME"):
            default_downtime=open("/config/DEFAULT_DOWNTIME").read()
        if os.path.exists("/config/UPSCALE_PERIOD"):
            upscale_period=open("/config/UPSCALE_PERIOD").read()
        if os.path.exists("/config/DOWNSCALE_PERIOD"):
            downscale_period=open("/config/DOWNSCALE_PERIOD").read()
        if os.path.exists("/config/EXCLUDE_DEPLOYMENTS"):
            exclude_deployments=open("/config/EXCLUDE_DEPLOYMENTS").read()
        if os.path.exists("/config/DOWNTIME_REPLICAS"):
            downtime_replicas=open("/config/DOWNTIME_REPLICAS").read()
        try:
            scale(
                namespace,
                upscale_period,
                downscale_period,
                default_uptime,
                default_downtime,
                include_resources=frozenset(include_resources.split(",")),
                exclude_namespaces=frozenset(exclude_namespaces.split(",")),
                exclude_deployments=frozenset(exclude_deployments.split(",")),
                dry_run=dry_run,
                grace_period=grace_period,
                downtime_replicas=downtime_replicas,
                deployment_time_annotation=deployment_time_annotation,
            )
        except Exception as e:
            logger.exception(f"Failed to autoscale: {e}")
        if run_once or handler.shutdown_now:
            return
        with handler.safe_exit():
            time.sleep(interval)
