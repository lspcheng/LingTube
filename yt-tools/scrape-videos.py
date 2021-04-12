#!/usr/bin/env python3

import argparse, logging
from glob import glob
from csv import DictWriter
from pytube import YouTube, exceptions, helpers
from os import makedirs, path, walk, rename
from re import sub, findall
from time import sleep, strftime
from sys import argv


def write_captions(captions, video, yt_id, channel_name="", channel_id="", group=None, screen=None, convert_srt=False, include_title=False):
    """Write Caption object to a file. If an output folder is not specified, captions will be placed in a folder corresponding to the name of the video's author (i.e. channel).

    :param captions: The Caption track to download
    :param yt_id: YouTube ID string of the video from the url
    :param channel_name: The name of the channel as given on its main page (default "")
    :param channel_id: The name of the channel as it appears in the channel's URL (default "")
    :param group: The folder to output the caption track to (default None)
    :param convert_srt: Convert captions from XML to SRT format (default False)
    :param include_title: Include video title in caption filename (default True)

    :return success: 1 if captions were downloaded successfully, 0 otherwise
    """

    safe_title = helpers.safe_filename(video.title)
    out_path = ""

    out_path = path.join("corpus", "raw_subtitles")
    if group is not None:
        out_path = path.join(out_path, group)

    if "a." in captions.code:
        out_path = path.join(out_path, "auto", captions.code.split(".")[1])
    else:
        out_path = path.join(out_path, "manual", captions.code.split(".")[0])

    punc_and_whitespace = "[\s\_\-\.\?\!,;:'\"\\\/]+"
    # non_alphanumeric = r"[^A-Za-z1-9]"
    if channel_name and channel_id:
        safe_channel_name = sub(punc_and_whitespace, "", channel_name)
        safe_author = "{0}_{1}".format(safe_channel_name, channel_id)
    else:
        safe_author = sub(punc_and_whitespace, "", video.author)

    out_path = path.join(out_path, safe_author)

    if not path.exists(out_path):
        makedirs(out_path)

    try:
        if include_title:
            captions.download(helpers.safe_filename(safe_title), srt=convert_srt, output_path=out_path, filename_prefix="{0}_{1}_".format(safe_author, yt_id))
            return 1
        else:
            captions.download(str(yt_id), srt=convert_srt, output_path=out_path, filename_prefix="{0}_".format(safe_author))
            return 1
    except:
        logging.critical("Video {0}: Could not download caption track for video {0} from channel {1} ({2})".format(yt_id, video.author, video.title))
        return 0


def write_audio(audio, video, yt_id, channel_name="", channel_id="", group=None, screen=None, include_title=False):
    """Write audio Stream object to a file. If an output folder is not specified, audio will be placed in a folder corresponding to the name of the video's author (i.e. channel).

    :param audio: The audio Stream to download
    :param yt_id: YouTube ID string of the video from the url
    :param channel_name: The name of the channel as given on its main page (default "")
    :param channel_id: The name of the channel as it appears in the channel's URL (default "")
    :param group: The folder to output the audio stream to (default None)
    :param include_title: Include video title in audio filename (default True)
    """

    safe_title = helpers.safe_filename(video.title)
    safe_author = helpers.safe_filename(video.author)

    out_path = path.join("corpus", "raw_audio")
    if group is not None:
        out_path = path.join(out_path, group)

    punc_and_whitespace = "[\s\_\-\.\?\!,;:'\"\\\/]+"
    # non_alphanumeric = r"[^A-Za-z1-9]"
    if channel_name and channel_id:
        safe_channel_name = sub(punc_and_whitespace, "", channel_name)
        safe_author = "{0}_{1}".format(safe_channel_name, channel_id)
    else:
        safe_author = sub(punc_and_whitespace, "", video.author)

    out_path = path.join(out_path, safe_author)

    if not path.exists(out_path):
        makedirs(out_path)

    try:
        if include_title:
            audio.download(filename=safe_title, output_path=out_path, filename_prefix="{0}_{1}_".format(safe_author, yt_id), skip_existing=True)
        else:
            audio.download(filename=str(yt_id), output_path=out_path, filename_prefix="{0}_".format(safe_author), skip_existing=True)

    except:
        logging.critical("Video {0}: Could not save audio stream for video {0} from channel {1} ({2})".format(yt_id, video.author, video.title))

    # Be polite
    sleep(1)


def write_captions_by_language(video, yt_id, channel_name="", channel_id="", language=None, group=None, screen=None, include_auto=False, convert_srt=False, include_title=False):
    """Filter captions by language and write each caption track to a file. If no language is specified, all caption tracks will be downloaded.

    :param video: The YouTube object to download caption tracks from
    :param yt_id: YouTube ID string of the video from the url
    :param channel_name: The name of the channel as given on its main page (default "")
    :param channel_id: The name of the channel as it appears in the channel's URL (default "")
    :param language: The language to download caption tracks for (default None)
    :param group: The folder to output the caption track to (default None)
    :param convert_srt: Convert captions from XML to SRT format (default False)
    :param include_title: Include video title in caption filename (default False)

    :return caption_list: list of metadata for all successfully-downloaded caption tracks
    """

    caption_list = []
    for track in video.captions:
        if language is None or (language in track.name and (include_auto or "a." not in track.code)):

            success = write_captions(track, video, yt_id, channel_name, channel_id, group, screen, convert_srt, include_title)
            if success:
                caption_list.append((track.code, track.name))

            # Be polite
            sleep(1)

    return caption_list


def write_metadata(video, yt_id, caption_list, log_writer, url, channel_name="", channel_id=""):
    """Write video metadata to log file.

    :param video: The YouTube object to log
    :param yt_id: YouTube ID string of the video from the url
    :param caption_list: A list of successfully-downloaded captions
    :param log_writer: DictWriter to use for writing metadata
    :param channel_name: The name of the channel as given on its main page (default "")
    :param channel_id: The name of the channel as it appears in the channel's URL (default "")
    """

    metadata = {
        "yt_id": yt_id,
        "author": video.author,
        "name": channel_name,
        "ID": channel_id,
        "url": url,
        "title": video.title,
        "description": video.description.replace('\n', ' '),
        "keywords": video.keywords,
        "length": video.length,
        "publish_date": video.publish_date,
        "views": video.views,
        "rating": video.rating,
        "captions": caption_list
    }

    log_writer.writerow(metadata)


def process_video(video, channel_dict, log_writer, channel_name=None, channel_id=None, url=None, language=None, group=None, screen=None, include_audio=False, include_auto=False, convert_srt=False, include_title=False):
    """Download captions, audio (optional), and metadata for a given video.

    :param video: The YouTube object to process
    :param channel_name: The name of the channel as given on its main page (default None)
    :param channel_id: The name of the channel as it appears in the channel's URL (default None)
    :param channel_id: The url of the video
    :param yt_id: YouTube ID string of the video from the url
    :param language: The language to download caption tracks for (default None)
    :param group: The folder to output the caption track to (default None)
    :param convert_srt: Convert captions from XML to SRT format (default False)
    :param include_title: Include video title in caption filename (default False)

    :return caption_dict: list of metadata for all successfully-downloaded caption tracks
    """

    if video.author not in channel_dict.keys():
        channel_dict.update({video.author: 0})
    channel_dict[video.author] = channel_dict[video.author] + 1

    punc_and_whitespace = "[\s\_\-\.\?\!,;:'\"\\\/]+"
    yt_id = sub(punc_and_whitespace, '',
                    findall(r".+watch\?v=(.+)\b", url)[0])

    caption_list = write_captions_by_language(video, position, channel_name, channel_id, language, group, include_auto, convert_srt, include_title)

    if include_audio:
        audio = video.streams.filter(mime_type="audio/mp4").first()
        write_audio(audio, video, yt_id, channel_name, channel_id, group, screen, include_title)

    if len(caption_list):
        write_metadata(video, yt_id, caption_list, log_writer, url, channel_name, channel_id)

    return channel_dict


def process_videos(urls_path, batch=False, language=None, group=None, screen=None,  include_audio=False, include_auto=False, convert_srt=False, include_titles=False, resume_from=0, limit_to=-1):
    """Download captions, audio (optional), and metadata for a list of videos.

    :param batch: Indicates if a directory or single file is being processed
    :param video: Path to a file containing the list of URLs to process
    :param channel_name: The name of the channel as given on its main page (default None)
    :param channel_id: The name of the channel as it appears in the channel's URL (default None)
    :param language: The language to download caption tracks for (default None)
    :param group: The subfolder to output the caption and audio tracks to (default None)
    :param include_audio: Download audio in addition to captions (default False)
    :param include_auto: Download automatically-generated captions (default False)
    :param convert_srt: Convert captions from XML to SRT format (default False)
    :param include_titles: Include video titles in caption filenames (default False)
    :param resume_from: Start from the Nth entry in the URL list (default 0)
    :param limit_to: Download captions (and audio) from only N files (default -1)
    """

    channel_dict = {}
    video_count = 0

    if group is None:
        log_fn = "{0}_log.csv".format(path.splitext(path.split(urls_path)[1])[0])
    else:
        log_fn = "{0}_log.csv".format(group)

    write_type = 'w'
    if batch and group:
        write_type = 'a'

    with open(urls_path, "r") as urls_in, open(log_file, write_type) as log_out:

        # Prepare writer for writing video data
        log_writer = DictWriter(log_out, fieldnames=["yt_id", "author", "name", "ID", "url", "title", "description", "keywords", "length", "publish_date", "views", "rating", "captions"])
        if not (batch and group):
            log_writer.writeheader()

        for url_data in urls_in:

            video_count += 1

            if(video_count < resume_from):
                continue

            url_data = url_data.strip('\n').split('\t')
            # Get URL and title
            if len(url_data) == 3:
                (url, channel_name, channel_id) = url_data
            elif len(url_data) == 1:
                url = url_data[0]
                channel_name=None
                channel_id=None
            else:
                logging.critical("Invalid file format")
                exit(2)

            # Try to load the video
            try:
                video = YouTube(url)
            except KeyError as e:
                logging.warning("Video {0}: Could not retrieve URL ({1})".format(video_count, url))
                continue
            except exceptions.VideoUnavailable as e:
                logging.warning("Video {0}: Video unavailable ({1})".format(video_count, url))
                continue
            # except:
            #     logging.critical("Video {0}: An unexpected error occured ({1})".format(video_count, url))
            #     continue

            process_video(video, channel_dict, log_writer, channel_name, channel_id, url, language, group, screen, include_audio, include_auto, convert_srt, include_titles)

            if limit_to != -1 and video_count == resume_from + limit_to:
                print("{0}: Limit reached".format(urls_path))
                break


def process_files(urls_path, language=None, group=None, screen=None, include_audio=False, include_auto=False, convert_srt=False, include_titles=False, resume_from=0, limit_to=-1):
    """Download captions, audio (optional), and metadata from a directoy of video lists.

    :param video: Path to a directory containing a set of list files
    :param channel_name: The name of the channel as given on its main page (default None)
    :param channel_id: The name of the channel as it appears in the channel's URL (default None)
    :param language: The language to download caption tracks for (default None)
    :param group: The subfolder to output the caption and audio tracks to (default None)
    :param include_audio: Download audio in addition to captions (default False)
    :param include_auto: Download automatically-generated captions (default False)
    :param convert_srt: Convert captions from XML to SRT format (default False)
    :param include_titles: Include video titles in caption filenames (default False)
    :param resume_from: Start from the Nth entry in the URL list (default 0)
    :param limit_to: Download captions (and audio) from only N files (default -1)
    """

    URL_fns_txt = sorted(glob(path.join(urls_path, "*.txt")))
    URL_fns_csv = sorted(glob(path.join(urls_path, "*.csv")))

    if group:
        log_fn = "{0}_log.csv".format(group)
        with open(path.join("corpus", "logs", log_fn), 'w') as log_out: # Overwrite file in a hacky way
            log_writer = DictWriter(log_out, fieldnames=["position", "author", "name", "ID", "url", "title", "description", "keywords", "length", "publish_date", "views", "rating", "captions"])
            log_writer.writeheader()

    all_fns = URL_fns_txt + URL_fns_csv

    for fn in all_fns:
        process_videos(fn, True, language, group, include_audio, include_auto, convert_srt, include_titles, resume_from, limit_to)


def main(args):

    if not path.isfile(args.urls_in) and not path.isdir(args.urls_in):
        logging.error("url_list must be a file or directory")
        exit(2)

    if not path.exists(path.join("corpus", "logs")):
        makedirs(path.join("corpus", "logs"))

    if(args.resume):
        print("Resuming from video {0}".format(args.resume))

    if path.isfile(args.urls_in):
        process_videos(args.urls_in, False, args.language, args.group, args.audio, args.auto, args.srt, args.titles, args.resume, args.limit)

    if path.isdir(args.urls_in):
        process_files(args.urls_in, args.language, args.group, args.audio, args.auto, args.srt, args.titles, args.resume, args.limit)

    for dirpath, dirnames, files in walk(path.join('corpus', 'raw_subtitles')):
         for filename in files:
             name, ext = path.splitext(filename)
             if ext == '.srt':
                 clean_filename = name.rsplit(' ',1)[0]+ext
                 rename(path.join(dirpath, filename),
                           path.join(dirpath, clean_filename))


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Download available subtitles and audio from a list of YouTube video urls.')

    parser.add_argument('urls_in', type=str, help='path to a file or directory containing the URLs to scrape')

    parser.add_argument('--language', '-l', default=None, type=str, help='filter captions by language name (e.g. "Korean"); if unspecified, all captions will be downloaded')
    parser.add_argument('--group',    '-g', default=None, metavar='NAME', type=str, help='a name for the group; if unspecified, channel names will be used')

    parser.add_argument('--auto',     '-a', action='store_true', default=False, help='include automatically-generated captions')
    parser.add_argument('--audio',    '-s', action='store_true', default=False, help='download audio')
    parser.add_argument('--titles',   '-t', action='store_true', default=False, help='include video titles in caption and audio filenames')
    parser.add_argument('--srt',            action='store_true', default=False, help='download captions in SRT format')

    parser.add_argument('--resume', '-res', type=int, metavar='N', default=0,  help='resume downloading from Nth video or file')
    parser.add_argument('--limit',  '-lim', type=int, metavar='N', default=-1, help='limit processing to N videos or files')

    args = parser.parse_args()

    main(args)
