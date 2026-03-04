import datetime
import json
import logging

from solnlib import conf_manager, log
from solnlib.modular_input import checkpointer
from splunklib import modularinput as smi
from exoscale.api.v2 import Client


ADDON_NAME = "SA-Exoscale_fs"


def logger_for_input(input_name: str) -> logging.Logger:
    return log.Logs().get_logger(f"{ADDON_NAME.lower()}_{input_name}")


def get_account_argument(
    session_key: str, account_name: str, account_argument: str
) -> str:
    cfm = conf_manager.ConfManager(
        session_key,
        ADDON_NAME,
        realm=f"__REST_CREDENTIAL__#{ADDON_NAME}#configs/conf-sa-exoscale_fs_account",
    )
    account_conf_file = cfm.get_conf("sa-exoscale_fs_account")
    return account_conf_file.get(account_name).get(account_argument)


def get_data_from_api(
    logger: logging.Logger,
    api_key: str,
    api_secret: str,
    from_date: datetime.datetime,
    to_date: datetime.datetime,
):
    from_time_formatted = from_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    to_time_formatted = to_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    logger.info(f"Fetching events from {from_time_formatted} to {to_time_formatted}")
    c = Client(api_key, api_secret)
    return c.list_events(**{"from": from_time_formatted, "to": to_time_formatted})


def validate_input(definition: smi.ValidationDefinition):
    return


def stream_events(inputs: smi.InputDefinition, event_writer: smi.EventWriter):
    for input_name, input_item in inputs.inputs.items():
        normalized_input_name = input_name.split("/")[-1]
        logger = logger_for_input(normalized_input_name)
        try:
            session_key = inputs.metadata["session_key"]
            log_level = conf_manager.get_log_level(
                logger=logger,
                session_key=session_key,
                app_name=ADDON_NAME,
                conf_name="sa-exoscale_fs_settings",
            )
            logger.setLevel(log_level)
            log.modular_input_start(logger, normalized_input_name)
            api_key = get_account_argument(
                session_key, input_item.get("account"), "api_key"
            )
            api_secret = get_account_argument(
                session_key, input_item.get("account"), "api_secret"
            )
            index = input_item.get("index")
            reset_checkpoint = input_item.get("reset_checkpoint")
            checkpoint = checkpointer.KVStoreCheckpointer(
                normalized_input_name, session_key, ADDON_NAME
            )
            last_fetch_checkpoint = checkpoint.get("last_fetch_event_checkpoint")
            if reset_checkpoint:
                last_fetch_checkpoint = None
                checkpoint.update("last_fetch_event_checkpoint", None)
            if last_fetch_checkpoint is None:
                start_date = input_item.get("date")
                if start_date is None:
                    from_time = datetime.datetime.now() - datetime.timedelta(days=30)
                else:
                    from_time = datetime.datetime.strptime(start_date, "%Y-%m-%d")
            else:
                from_time = datetime.datetime.fromtimestamp(last_fetch_checkpoint)
            to_time = datetime.datetime.now()
            sourcetype = "exoscale:event"
            counter = 0
            for event in get_data_from_api(
                logger, api_key, api_secret, from_time, to_time
            ):
                event_writer.write_event(
                    smi.Event(
                        data=json.dumps(event, ensure_ascii=False, default=str),
                        index=index,
                        sourcetype=sourcetype,
                    )
                )
                counter += 1
            log.events_ingested(
                logger,
                input_name,
                sourcetype,
                counter,
                input_item.get("index"),
                account=input_item.get("account"),
            )
            log.modular_input_end(logger, normalized_input_name)
            checkpoint.update("last_fetch_event_checkpoint", to_time.timestamp())
        except Exception as e:
            log.log_exception(
                logger,
                e,
                "Exoscale Audit Fetching Exception",
                msg_before="Exception raised while ingesting data for Exoscale Audit logs: ",
            )
