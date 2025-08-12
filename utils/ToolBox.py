from __future__ import annotations

import re
import secrets

import requests
import json

def send_youtube_search_request(query: str, continuation: str, params: str):
    json_body = {}

    if continuation != "":
        json_body["continuation"] = continuation
    else:
        json_body["query"] = query
        json_body["params"] = params

    json_body["context"] = {
        "request": {
            "internalExperimentFlags": [],
            "useSsl": True
        },
        "client": {
            "utcOffsetMinutes": 0,
            "hl": "en-GB",
            "gl": "IN",
            "clientName": "WEB",
            "originalUrl": "https://www.youtube.com",
            "clientVersion": "2.20250613.00.00",
            "platform": "DESKTOP"
        },
        "user": {
            "lockedSafetyMode": False
        }
    }

    headers = {
        "Origin": "https://www.youtube.com",
        "Referer": "https://www.youtube.com",
        "X-YouTube-Client-Version": "2.20250613.00.00",
        "X-YouTube-Client-Name": "1",
        "Content-Type": "application/json",
        "Accept-Language": "en-GB, en;q=0.9"
    }

    response = requests.post(
        "https://www.youtube.com/youtubei/v1/search?prettyPrint=false",
        headers=headers,
        data=json.dumps(json_body),
        timeout=20
    )

    response.raise_for_status()  # raise exception if request failed
    response_json = response.json()

    total_videos = []
    total_result = {}

    estimated_result = response_json.get("estimatedResults", "")
    total_result["estimatedResult"] = estimated_result

    # First block: "contents"
    if "contents" in response_json:
        contents_array = deep_get(
            response_json,
            "contents",
            "twoColumnSearchResultsRenderer",
            "primaryContents",
            "sectionListRenderer",
            "contents", 0,
            "itemSectionRenderer",
            "contents"
        )

        if isinstance(contents_array, list):
            for item in contents_array:
                if "videoRenderer" in item:
                    total_videos.append(create_video_tree(item["videoRenderer"]))
                if "reelShelfRenderer" in item:
                    shorts = item["reelShelfRenderer"]["items"]
                    for short_item in shorts:
                        total_videos.append(extract_shorts_info(short_item))

            continuation_token = deep_get(
                response_json,
                "contents",
                "twoColumnSearchResultsRenderer",
                "primaryContents",
                "sectionListRenderer",
                "contents", 1,
                "continuationItemRenderer",
                "continuationEndpoint",
                "continuationCommand",
                "token"
            )

            total_result["continuation"] = continuation_token
            total_result["videos"] = total_videos

    # Second block: "onResponseReceivedCommands"
    if "onResponseReceivedCommands" in response_json:
        contents_array = deep_get(
            response_json,
            "onResponseReceivedCommands", 0,
            "appendContinuationItemsAction",
            "continuationItems", 0,
            "itemSectionRenderer",
            "contents"
        )

        if isinstance(contents_array, list):
            for item in contents_array:
                if "videoRenderer" in item:
                    vt = create_video_tree(item["videoRenderer"])
                    if vt not in total_videos:
                        total_videos.append(vt)
                if "reelShelfRenderer" in item:
                    shorts = item["reelShelfRenderer"]["items"]
                    for short_item in shorts:
                        mk = extract_shorts_info(short_item)
                        if mk not in total_videos:
                            total_videos.append(mk)

        continuation_token = deep_get(
            response_json,
            "onResponseReceivedCommands", 0,
            "appendContinuationItemsAction",
            "continuationItems", 1,
            "continuationItemRenderer",
            "continuationEndpoint",
            "continuationCommand",
            "token"
        )

        total_result["continuation"] = continuation_token
        total_result["videos"] = total_videos

    return total_result


def extract_shorts_info(json_obj: dict) -> dict:
    root = json_obj["shortsLockupViewModel"]
    video_id = root["inlinePlayerData"]["onVisible"]["innertubeCommand"]["watchEndpoint"]["videoId"]
    title = root["overlayMetadata"]["primaryText"]["content"]
    return {
        "videoId": video_id,
        "title": title,
        "duration": "short"
    }


def deep_get(obj, *keys):
    current = obj
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key)
        elif isinstance(current, list) and isinstance(key, int):
            if 0 <= key < len(current):
                current = current[key]
            else:
                return None
        else:
            return None
    return current


def create_video_tree(video_renderer: dict) -> dict:
    video_id = video_renderer["videoId"]
    title = video_renderer["title"]["runs"][0]["text"]
    duration = video_renderer.get("lengthText", {}).get("simpleText", "Unknown")
    return {
        "videoId": video_id,
        "duration": duration,
        "title": title
    }

def txt2filename(txt: str) -> str:
    special_characters = [
        "@", "#", "$", "*", "&", "<", ">", "/", "\b", "|", "?", "CON", "PRN", "AUX", "NUL",
        "COM0", "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9", "LPT0",
        "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9", ":", "\"", "'"
    ]

    normal_string = txt
    for sc in special_characters:
        normal_string = normal_string.replace(sc, "")

    return normal_string
def convert_bytes( size_in_bytes: int) -> str:
    kilobyte = 1024
    megabyte = kilobyte * 1024
    gigabyte = megabyte * 1024

    if size_in_bytes >= gigabyte:
        return f"{size_in_bytes / gigabyte:.2f} GB"
    elif size_in_bytes >= megabyte:
        return f"{size_in_bytes / megabyte:.2f} MB"
    elif size_in_bytes >= kilobyte:
        return f"{size_in_bytes / kilobyte:.2f} KB"
    else:
        return f"{size_in_bytes} Bytes"
def getStreamingData(videoId):

    visitor_data = get_visitor_id()
    # cpn or nonce string will return in each format url
    cpn = RandomStringGenerator.generate_content_playback_nonce()
    # t parameter used for what i dont know
    tp = RandomStringGenerator.generate_t_parameter()
    response = android_player_response(cpn, visitor_data, videoId, tp)
    return response

def extract_video_id( yt_url: str) -> str | None:
    regex = r"""^.*(?:(?:youtu\.be\/|v\/|vi\/|u\/\w\/|embed\/|shorts\/|live\/)|(?:(?:watch)?\?v(?:i)?=|\&v(?:i)?=))([^#\&\?]*).*"""
    match_result = re.match(regex, yt_url)
    if match_result:
        return match_result.group(1)
    return None

def android_player_response(cpn: str, visitor_data: str, video_id: str, t: str) -> requests.Response:
    url = f"https://youtubei.googleapis.com/youtubei/v1/reel/reel_item_watch?prettyPrint=false&t={t}&id={video_id}&fields=playerResponse"

    # JSON request body
    json_body = {
        "cpn": cpn,
        "contentCheckOk": True,
        "context": {
            "request": {
                "internalExperimentFlags": []
            },
            "client": {
                "androidSdkVersion": 35,
                "utcOffsetMinutes": 0,
                "osVersion": "15",
                "hl": "en-GB",
                "clientName": "ANDROID",
                "gl": "GB",
                "clientScreen": "WATCH",
                "clientVersion": "19.28.35",
                "osName": "Android",
                "platform": "MOBILE",
                "visitorData": visitor_data
            },
            "user": {
                "lockedSafetyMode": False
            }
        },
        "racyCheckOk": True,
        "videoId": video_id,
        "playerRequest": {
            "videoId": video_id
        },
        "disablePlayerResponse": False
    }

    # Request headers
    headers = {
        "User-Agent": "com.google.android.youtube/19.28.35 (Linux; U; Android 15; GB) gzip",
        "X-Goog-Api-Format-Version": "2",
        "Content-Type": "application/json",
        "Accept-Language": "en-GB, en;q=0.9"
    }

    # Send the request
    response = requests.post(url, headers=headers, data=json.dumps(json_body))
    return response


def get_visitor_id() -> str:
    url = "https://youtubei.googleapis.com/youtubei/v1/visitor_id?prettyPrint=false"

    # JSON request body
    json_body = {
        "context": {
            "request": {
                "internalExperimentFlags": []
            },
            "client": {
                "androidSdkVersion": 35,
                "utcOffsetMinutes": 0,
                "osVersion": "15",
                "hl": "en-GB",
                "clientName": "ANDROID",
                "gl": "GB",
                "clientScreen": "WATCH",
                "clientVersion": "19.28.35",
                "osName": "Android",
                "platform": "MOBILE"
            },
            "user": {
                "lockedSafetyMode": False
            }
        }
    }

    headers = {
        "User-Agent": "com.google.android.youtube/19.28.35 (Linux; U; Android 15; GB) gzip",
        "X-Goog-Api-Format-Version": "2",
        "Content-Type": "application/json",
        "Accept-Language": "en-GB, en;q=0.9"
    }

    response = requests.post(url, headers=headers, data=json.dumps(json_body))

    if response.status_code == 200:
        response_json = response.json()
        return response_json["responseContext"]["visitorData"]
    else:
        raise Exception(f"Failed to get visitor ID: {response.status_code} - {response.text}")


class RandomStringGenerator:
    ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"

    @staticmethod
    def generate_content_playback_nonce() -> str:
        return RandomStringGenerator._generate(RandomStringGenerator.ALPHABET, 16)

    @staticmethod
    def generate_t_parameter() -> str:
        return RandomStringGenerator._generate(RandomStringGenerator.ALPHABET, 12)

    @staticmethod
    def _generate(alphabet: str, length: int) -> str:
        return ''.join(secrets.choice(alphabet) for _ in range(length))







