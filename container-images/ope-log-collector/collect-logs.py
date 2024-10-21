import os
import logging
from kubernetes_asyncio import client, config, watch
import aiofiles
import asyncio
import traceback


LOG = logging.getLogger(__name__)
logging.basicConfig(level='INFO', format='%(message)s')


async def get_client() -> client.CoreV1Api:
    try:
        await config.load_config()
        return client.CoreV1Api()
    except config.ConfigException as e:
        LOG.error('Could not configure Kubernetes client: %s', str(e))
        exit(1)


async def gather_logs(namespace: str):
    v1 = await get_client()

    while True:
        w = watch.Watch()
        log_tasks = {}
        event_tasks = {}
        pvc_tasks = {}
        try:
            async for event in w.stream(
                v1.list_namespaced_pod, namespace=namespace, timeout_seconds=0
            ):
                pod = event['object']
                pod_name = pod.metadata.name
                event_type = event['type']

                # Filter pods created by rhoai
                if not pod_name.startswith('jupyter-nb'):
                    continue

                pvc_name = pod.spec.volumes[0].name

                # Wait until pods start up
                if event_type in ['ADDED', 'MODIFIED']:
                    pod_status = pod.status.phase
                    if pod_status != 'Running':
                        continue

                    container_name = pod.spec.containers[0].name

                    # Start streaming logs
                    if pod_name not in log_tasks:
                        log_tasks[pod_name] = asyncio.create_task(
                            stream_pod_logs(v1, namespace, pod_name, container_name)
                        )
                        event_tasks[pod_name] = asyncio.create_task(
                            stream_pod_events(v1, namespace, pod_name)
                        )
                        pvc_tasks[pod_name] = asyncio.create_task(
                            stream_pvc_events(v1, namespace, pod_name, pvc_name)
                        )
                elif event_type == 'DELETED':
                    LOG.info(f'Pod deleted: {pod_name}. Cancelling log streaming.')
                    if pod_name in log_tasks:
                        log_tasks[pod_name].cancel()
                        del log_tasks[pod_name]
                    if pod_name in event_tasks:
                        event_tasks[pod_name].cancel()
                        del event_tasks[pod_name]
                    if pod_name in pvc_tasks:
                        pvc_tasks[pod_name].cancel()
                        del pvc_tasks[pod_name]

        except Exception as e:
            LOG.info(f'Server side Timeout: {e}. Re-establishing connection.')

            await w.close()

            for task in log_tasks.values():
                task.cancel()

            for event in event_tasks.values():
                event.cancel()

            for event in pvc_tasks.values():
                event.cancel()

            await asyncio.gather(*log_tasks.values(), return_exceptions=True)

            await asyncio.gather(*event_tasks.values(), return_exceptions=True)

            await asyncio.gather(*pvc_tasks.values(), return_exceptions=True)

            await asyncio.sleep(5)


async def stream_pod_logs(
    v1: client.CoreV1Api, namespace: str, pod_name: str, container_name: str
):
    LOG_DIR = './log'

    if not os.path.exists(LOG_DIR):
        try:
            os.makedirs(LOG_DIR)
        except Exception as e:
            LOG.error(f"Could not create log directory '{LOG_DIR}': {e}")
            exit(1)

    log_file_path = os.path.join(LOG_DIR, f'{pod_name}.log')
    LOG.info(f"Streaming logs for pod '{pod_name}' to '{log_file_path}'.")

    response = None
    try:
        response = await v1.read_namespaced_pod_log(
            name=pod_name,
            namespace=namespace,
            container=container_name,
            follow=True,
            _preload_content=False,
            timestamps=True,
        )

        # Read logs and write to log file
        async with aiofiles.open(log_file_path, 'w') as log_file:
            async for line in response.content:
                if line:
                    decoded_line = line.decode('utf-8')
                    await log_file.write(decoded_line)
                    await log_file.flush()
    except asyncio.CancelledError:
        if response:
            await response.release()
    except Exception as e:
        LOG.error(f"Unexpected error while streaming logs for pod '{pod_name}': {e}")
        LOG.error(traceback.format_exc())
        raise
    finally:
        if response:
            await response.release()

    await asyncio.sleep(5)


async def stream_pod_events(v1: client.CoreV1Api, namespace: str, pod_name: str):
    LOG_DIR = './log'

    if not os.path.exists(LOG_DIR):
        try:
            os.makedirs(LOG_DIR)
        except Exception as e:
            LOG.error(f"Could not create log directory '{LOG_DIR}': {e}")
            exit(1)

    log_file_path = os.path.join(LOG_DIR, f'{pod_name}-pod-events.log')
    LOG.info(f"Streaming pod events for pod '{pod_name}' to '{log_file_path}'.")

    field_selector = f'involvedObject.kind=Pod,involvedObject.name={pod_name},involvedObject.namespace={namespace}'

    response = None
    try:
        events = await v1.list_namespaced_event(
            namespace=namespace, field_selector=field_selector
        )

        # Read logs and write to log file
        async with aiofiles.open(log_file_path, 'w') as log_file:
            for event in events.items:
                if event:
                    event_time = event.last_timestamp
                    event_type = event.type
                    event_message = event.message

                    event_entry = f'{event_time} | Type: {event_type} | Message: {event_message}\n'

                    await log_file.write(event_entry)
                    await log_file.flush()

    except asyncio.CancelledError:
        if response:
            await response.release()
    except Exception as e:
        LOG.error(f"Unexpected error while streaming events for pod '{pod_name}': {e}")
        LOG.error(traceback.format_exc())
        raise
    finally:
        if response:
            await response.release()

    await asyncio.sleep(5)


async def stream_pvc_events(
    v1: client.CoreV1Api, namespace: str, pod_name: str, pvc_name: str
):
    LOG_DIR = './log'

    if not os.path.exists(LOG_DIR):
        try:
            os.makedirs(LOG_DIR)
        except Exception as e:
            LOG.error(f"Could not create log directory '{LOG_DIR}': {e}")
            exit(1)

    log_file_path = os.path.join(LOG_DIR, f'{pod_name}-pvc-events.log')
    LOG.info(f"Streaming pvc events for pod '{pod_name}' to '{log_file_path}'.")

    field_selector = f'involvedObject.kind=PersistentVolumeClaim,involvedObject.name={pvc_name},involvedObject.namespace={namespace}'

    response = None
    try:
        events = await v1.list_namespaced_event(
            namespace=namespace, field_selector=field_selector
        )

        # Read logs and write to log file
        async with aiofiles.open(log_file_path, 'w') as log_file:
            for event in events.items:
                if event:
                    event_time = event.last_timestamp
                    event_type = event.type
                    event_message = event.message

                    event_entry = f'{event_time} | Type: {event_type} | Message: {event_message}\n'

                    await log_file.write(event_entry)
                    await log_file.flush()

    except asyncio.CancelledError:
        if response:
            await response.release()
    except Exception as e:
        LOG.error(
            f"Unexpected error while streaming pvc events for pod '{pod_name}': {e}"
        )
        LOG.error(traceback.format_exc())
        raise
    finally:
        if response:
            await response.release()

    await asyncio.sleep(5)


if __name__ == '__main__':
    namespace_name = os.environ.get('NAMESPACE', 'rhods-notebooks')

    if not namespace_name:
        LOG.error('NAMESPACE environment variable is required.')
        exit(1)

    asyncio.run(gather_logs(namespace_name))
