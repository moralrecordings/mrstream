
import asyncio
import os

from . import twitch


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
            doc.write(f"{stream.title}\n")
            doc.write("="*len(stream.title) + "\n")
            doc.write("\n")
            doc.write(f":date: {ts.strftime('%Y-%m-%d')}\n")
            doc.write(f":category: Video\n")
            doc.write(f":tags: video, reversing, twitch\n")
            doc.write(":status: published\n\n\n")
            doc.write(".. raw:: html\n\n")
            doc.write("    <div class=\"responsive-embed widescreen\">\n")
            doc.write(f"        <iframe src=\"https://player.twitch.tv/?video=v{stream.id}&autoplay=false&parent=moral.net.au&parent=www.moral.net.au\" width=\"560\" height=\"315\" allowfullscreen></iframe>\n")
            doc.write("    </div>\n")

