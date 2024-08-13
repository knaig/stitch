import os
import googleapiclient.discovery
import csv


# Replace with your own API key
API_KEY = os.getenv("YOUTUBE_API_KEY")

# Initialize YouTube API client
youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=API_KEY)

def search_channels(query, page_token=None):
    request = youtube.search().list(
        part="snippet",
        type="channel",
        q=query,
        maxResults=50,
        pageToken=page_token,
        regionCode="US",  # Assuming we're focusing on US-based English content
        relevanceLanguage="en"
    )
    response = request.execute()
    return response

def get_channel_details(channel_ids):
    request = youtube.channels().list(
        part="snippet,statistics,contentDetails",
        id=",".join(channel_ids)
    )
    response = request.execute()
    return response

def get_video_durations(uploads_playlist_id):
    video_ids = []
    next_page_token = None
    while True:
        playlist_request = youtube.playlistItems().list(
            part="contentDetails",
            playlistId=uploads_playlist_id,
            maxResults=50,
            pageToken=next_page_token
        )
        playlist_response = playlist_request.execute()
        video_ids.extend([item['contentDetails']['videoId'] for item in playlist_response['items']])
        next_page_token = playlist_response.get('nextPageToken')
        if not next_page_token:
            break
    
    if not video_ids:
        return 0, 0

    total_videos = len(video_ids)
    long_videos = 0

    for i in range(0, len(video_ids), 50):
        video_request = youtube.videos().list(
            part="contentDetails",
            id=",".join(video_ids[i:i+50])
        )
        video_response = video_request.execute()

        for video in video_response['items']:
            duration = video['contentDetails']['duration']
            # Convert ISO 8601 duration to seconds
            hours = minutes = seconds = 0
            duration = duration.replace('PT', '')
            if 'H' in duration:
                hours, duration = duration.split('H')
                hours = int(hours)
            if 'M' in duration:
                minutes, duration = duration.split('M')
                minutes = int(minutes)
            if 'S' in duration:
                seconds = int(duration.replace('S', ''))
            
            total_seconds = hours * 3600 + minutes * 60 + seconds

            if total_seconds >= 1800:  # 30 minutes = 1800 seconds
                long_videos += 1
    
    return total_videos, long_videos

# Define the CSV file name
csv_file = "youtube_channels.csv"

def main():
    categories = [
        "education", "spiritual", "life coach", 
        "fitness", "nutrition", "mental health", 
        "time management", "career coaching", "mindfulness", 
        "photography", "writing", "music lessons", 
        "small business", "marketing", "financial planning", 
        "tech reviews", "cybersecurity", 
        "cooking", "gardening", "DIY crafts", 
        "language learning", "travel", "outdoors", 
        "research", "STEM", "homeschooling", 
        "history", "culture", "parenting", 
        "gaming", "esports", "environment", 
        "legal", "compliance", "pet care"
    ]

    channel_limit_per_category = 30
    total_channels_found = 0
    overall_channel_limit = 20

    # Define the CSV file name
    csv_file = "youtube_channels.csv"

    # Open the CSV file in write mode
    with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)

        # Write the header row
        writer.writerow(["Channel Title", "Channel ID", "Subscribers", "Total Videos", "Videos over 30 mins", "Description", "URL"])

        for category in categories:
            next_page_token = None
            category_channels_found = 0
            while category_channels_found < channel_limit_per_category:
                response = search_channels(category, next_page_token)
                channel_ids = [item['id']['channelId'] for item in response['items']]
                
                channel_details = get_channel_details(channel_ids)
                
                for item in channel_details['items']:
                    subscriber_count = int(item['statistics'].get('subscriberCount', 0))
                    video_count = int(item['statistics'].get('videoCount', 0))
                    uploads_playlist_id = item['contentDetails']['relatedPlaylists']['uploads']
                    
                    if 5000 <= subscriber_count < 100000 and video_count >= 100:
                        language = item['snippet'].get('defaultLanguage', 'en')
                        if language == 'en':
                            total_videos, long_videos = get_video_durations(uploads_playlist_id)
                            
                            if total_videos >= 100 and long_videos >= 50:
                                # Write channel data to the CSV file
                                writer.writerow([
                                    item['snippet']['title'],
                                    item['id'],
                                    subscriber_count,
                                    total_videos,
                                    long_videos,
                                    item['snippet']['description'],
                                    f"https://www.youtube.com/channel/{item['id']}"
                                ])
                                category_channels_found += 1
                                total_channels_found += 1
                                if total_channels_found >= overall_channel_limit:
                                    break
                
                if total_channels_found >= overall_channel_limit or not response.get('nextPageToken'):
                    break
                next_page_token = response.get('nextPageToken')
            
            if total_channels_found >= overall_channel_limit:
                break


if __name__ == "__main__":
    main()
