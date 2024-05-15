
import asyncio
import os

from . import config, twitch


def update_website(base_path: str) -> None:
    cfg = config.get()
    for k in cfg.keys():
        if k.startswith("config.") and cfg[k]["type"] == "twitch":
            svc_name = k[7:]
            update_video_posts(svc_name, base_path)


def update_video_posts(name: str, base_path: str) -> None:
    streams = asyncio.get_event_loop().run_until_complete(twitch.get_past_streams(name))

    for stream in streams:
        ts = stream.created_at
        slug = f"{ts.strftime('%Y%m%d')}__stream"
        path = os.path.join(base_path, slug)
        if not os.path.exists(path):
            os.mkdir(path)
        if not os.path.isdir(path):
            print(f"Unable to write to {path}, skipping")
            continue
        with open(os.path.join(path, "article.rst"), "w") as doc:
            thumbnail = stream.thumbnail_url.replace("%{width}", "1200").replace("%{height}", "675")
            doc.write(f"{stream.title}\n")
            doc.write("="*len(stream.title) + "\n")
            doc.write("\n")
            doc.write(f":date: {ts.strftime('%Y-%m-%d')}\n")
            doc.write(f":category: Video\n")
            doc.write(f":tags: video, reversing, twitch\n")
            doc.write(":status: published\n\n\n")
            doc.write(f".. raw:: html\n\n")
            doc.write(f"    <a target=\"_blank\" href=\"{stream.url}\">\n\n")
            doc.write(f".. image:: {thumbnail}\n")
            doc.write(f"    :class: widescreen\n")
            doc.write(f"    :alt: Thumbnail for the stream titled \"{stream.title}\"\n")
            doc.write(f"    :title: Thumbnail for the stream titled \"{stream.title}\"\n\n")
            doc.write(f".. raw:: html\n\n")
            doc.write(f"    </a>\n\n")

