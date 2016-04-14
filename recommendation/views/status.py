from os import path

from celery.app.control import Control
from flask import Blueprint, jsonify, send_file
from redis.exceptions import ConnectionError as RedisConnectionError

from recommendation.memcached import memcached
from recommendation.views.static import STATIC_DIR


status = Blueprint('status', __name__)


@status.route('/__version__')
def version():
    return send_file(path.join(STATIC_DIR, 'version.json'))


@status.route('/__lbheartbeat__')
def lbheartbeat():
    return ('', 200)


class ServiceDown(RuntimeError):
    pass


def memcached_status():
    """
    Raises ServiceDown if the memcached server is down. `memcached.set` returns
    `True` if the operation was performed correctly, and `0` if not.
    """
    if not memcached.set('ping', 'pong'):
        raise ServiceDown()


def redis_status(app):
    """
    Raises ServiceDown if the Redis server used as a celery broker is down.
    Since our application should not have access to the Redis server, we test
    this by instantiating a Celery Control and attempting to ping it.
    """
    try:
        Control(app=app).ping(timeout=1)
    except RedisConnectionError:
        raise ServiceDown()


def celery_status(app):
    """
    Raises ServiceDown if any Celery worker servers are down, if any clusters
    have no workers, or if any workers are down.
    """
    clusters = Control(app=app).ping(timeout=1)
    if not clusters:
        raise ServiceDown()
    for cluster in clusters:
        if not cluster:
            raise ServiceDown()
        for host, status in cluster.items():
            if 'ok' not in status or status['ok'] != 'pong':
                raise ServiceDown()


@status.route('/__heartbeat__')
def heartbeat():
    """
    Sequentially runs each of the memcached, redis, and celery health checks.
    Returns a 500 if any raise ServiceDown, otherwise returns a 200 with an
    empty body.
    """
    celery, memcached, redis = True, True, True

    # create an shared celery app for testing
    from recommendation.factory import create_queue
    app = create_queue()

    try:
        celery_status(app)
    except ServiceDown:
        celery = False
    try:
        memcached_status()
    except ServiceDown:
        memcached = False
    try:
        redis_status(app)
    except ServiceDown:
        redis = False

    # close any opened connections to broker
    app.close()

    return jsonify({
        'celery': celery,
        'memcached': memcached,
        'redis': redis
    }), (200 if all([celery, memcached, redis]) else 500)
