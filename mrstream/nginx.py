import subprocess

from . import config


def update_config():
    cfg = config.get()
    with open(config.LOCAL_NGINX_PATH, "w") as f:
        for key in cfg.keys():
            if key.startswith("config."):
                svc_name = key[7:]
                if cfg[key]["enabled"] != "1":
                    continue
                f.write(f"push {cfg[key]['endpoint']};\n")
                

def run_server():
    # check for image
    if subprocess.call(["docker", "image", "inspect", "mrstream-nginx"]) != 0:
        raise RuntimeError("mrstream-nginx image not found!")

    update_config()

    subprocess.call(["docker", "run", "-it", f"--volume={config.LOCAL_NGINX_PATH}:/etc/nginx/push.conf", "--publish=1935:1935", "--publish=19350:19350", "mrstream-nginx:latest"])
