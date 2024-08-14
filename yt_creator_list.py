import os
import googleapiclient.discovery
import csv

# Replace with your own API key
API_KEY = os.getenv("YT_API_KEY_LIVLYFE")  #This is for livlyfe.in. Change this to "YOUTUBE_API_KEY" when using karthik.naig@gmail account

# Initialize YouTube API client
youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=API_KEY)

# Keywords to filter out organizations and Islamic-related content
organization_keywords = ["Inc", "Corp", "LLC", "Company", "Organization", "Group", "Foundation", "Association", "Official", "University"]
islamic_keywords = ["Islam", "Muslim", "Quran", "Hadith", "Sharia", "Ummah", "Allah", "Muhammad", "Ramadan", "Hajj"]

# File to store processed channel IDs
processed_channels_file = "processed_channels.txt"

# Thresholds and limits (can be easily modified)
MIN_SUBSCRIBERS = 5000
MAX_SUBSCRIBERS = 100000
MIN_VIDEOS = 50
MIN_LONG_VIDEOS = 30
LONG_VIDEO_THRESHOLD_SECONDS = 1800  # 30 minutes
CHANNEL_BATCH_SIZE = 50
CHANNEL_LIMIT_PER_CATEGORY = 30
OVERALL_CHANNEL_LIMIT = 1000

# Load processed channel IDs
if os.path.exists(processed_channels_file):
    with open(processed_channels_file, 'r') as f:
        processed_channels = set(f.read().splitlines())
else:
    processed_channels = set()

def is_individual_channel(title, description):
    # Skip channels with empty descriptions
    if not description:
        return False

    # Filter out "Topic" channels
    if "Topic" in title:
        return False

    # Filter out channels with organization or Islamic-related keywords
    for keyword in organization_keywords + islamic_keywords:
        if keyword.lower() in title.lower() or keyword.lower() in description.lower():
            return False

    return True


def matches_category(description, keywords):
    description_lower = description.lower()
    for category, keyword_list in keywords.items():
        for keyword in keyword_list:
            if keyword.lower() in description_lower:
                return True
    return False

def search_channels(page_token=None):
    print("Searching channels...")

    request = youtube.search().list(
        part="snippet",
        type="channel",
        maxResults=CHANNEL_BATCH_SIZE,
        pageToken=page_token,
        relevanceLanguage="en"  # Keep this to ensure English content
    )
    response = request.execute()
    return response

def get_channel_details(channel_ids):
    print(f"Fetching details for channels: {', '.join(channel_ids)}")
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
            maxResults=CHANNEL_BATCH_SIZE,
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

    for i in range(0, len(video_ids), CHANNEL_BATCH_SIZE):
        video_request = youtube.videos().list(
            part="contentDetails",
            id=",".join(video_ids[i:i+CHANNEL_BATCH_SIZE])
        )
        video_response = video_request.execute()

        for video in video_response['items']:
            if 'duration' not in video['contentDetails']:
                continue  # Skip videos without duration information

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

            if total_seconds >= LONG_VIDEO_THRESHOLD_SECONDS:
                long_videos += 1
    
    return total_videos, long_videos

def main():
    # Categories and associated keywords

    keywords = {        
        "career_development": [
            "life coach", "career coaching", "time management", "productivity", 
            "professional development", "leadership", "management", "skills training", 
            "career advice", "job search", "resume building", "interview skills", 
            "public speaking", "entrepreneurship", "networking"
        ],
        "arts_hobbies": [
            "photography", "writing", "music lessons", "art", "drawing", "painting", 
            "crafts", "DIY crafts", "handmade", "sculpting", "design", "graphic design", 
            "interior design", "fashion", "sewing", "knitting", "gardening", 
            "cooking", "baking", "culinary arts", "food"
        ],
        "business_finance": [
            "business", "finance", "financial planning", "investing", "investment", 
            "personal finance", "money management", "entrepreneurship", "startups", 
            "small business", "business strategy", "business management", 
            "marketing", "digital marketing", "sales", "business development", 
            "e-commerce", "online business", "lead generation", "branding", 
            "consulting", "venture capital", "angel investing", "crowdfunding", 
            "real estate", "property investment", "retirement planning", 
            "wealth management", "taxes", "tax planning", "accounting", 
            "bookkeeping", "stock market", "trading", "bonds", 
            "mutual funds", "ETFs", "portfolio management", "risk management", 
            "financial independence", "budgeting", "credit management", 
            "debt management", "insurance", "life insurance", "health insurance", 
            "estate planning", "legacy planning", "cryptocurrency", "blockchain", 
            "financial literacy", "corporate finance", "mergers", "acquisitions", 
            "business law", "contract law", "tax law", "economics", 
            "macroeconomics", "microeconomics", "supply chain management", 
            "inventory management", "logistics", "international trade", 
            "export", "import", "market analysis", "competitive analysis", 
            "business analytics", "data analytics", "business intelligence", 
            "customer relationship management", "CRM", "financial statements", 
            "balance sheet", "income statement", "cash flow", "profit and loss"
        ],
        "technology_reviews": [
            "tech reviews", "cybersecurity", "gadgets", "electronics", 
            "consumer electronics", "hardware", "device reviews", "product reviews"
        ],
        "travel_outdoors": [
            "travel", "outdoors", "adventure", "hiking", "camping", 
            "nature", "wildlife", "exploration", "backpacking", "eco-tourism"
        ],
        "gaming_esports": [
            "gaming", "esports", "video games", "gameplay", "streaming", 
            "gaming culture", "competitive gaming", "gaming news", "game reviews"
        ],
        "environment_legal_petcare": [
            "environment", "sustainability", "conservation", "green living", 
            "legal", "law", "compliance", "rights", "justice", "pet care", 
            "pets", "animals", "veterinary", "animal health"
        ],
        "education": [
            "education", "learning", "knowledge", "teaching", "tutoring", "training", "courses", 
            "classes", "study", "lessons", "homework", "tutorials", "mathematics", "science", 
            "physics", "chemistry", "biology", "literature", "history", "geography", 
            "economics", "sociology", "philosophy", "psychology", "anthropology", 
            "politics", "mathematics", "STEM", "engineering", "electronics", 
            "robotics", "data science", "research", "homeschooling", 
            "culture", "parenting", "learning", "STEM"
        ],

        "health_fitness_wellness": [
            "health", "wellness", "medicine", "meditation", "mental health", "fitness", 
            "nutrition", "exercise", "workout", "yoga", "pilates", "weight loss", 
            "diet", "healthy eating", "well-being", "sleep", "stress management", 
            "self-care", "mental fitness", "therapy", "counseling", "self-improvement", 
            "rehabilitation"
        ],
        "spirituality": [
            "spiritual", "spirituality", "mindfulness", "meditation", "yoga", "holistic", 
            "self-awareness", "inner peace", "consciousness", "enlightenment", "well-being", 
            "mental clarity", "emotional balance", "personal growth", "self-realization", 
            "healing", "energy", "chakra", "soul", "life purpose"
        ]
    }


    total_channels_found = 0

    # Define the CSV file name
    csv_file = "youtube_channels.csv"
    
    # Open the CSV file in append mode
    with open(csv_file, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)

        # Write the header row only if the file is empty
        if os.stat(csv_file).st_size == 0:
            writer.writerow(["Channel Title", "Channel ID", "Subscribers", "Total Videos", "Videos over 30 mins", "Description", "URL"])

        next_page_token = None
        while total_channels_found < OVERALL_CHANNEL_LIMIT:
            response = search_channels(next_page_token)
            channel_ids = [item['id']['channelId'] for item in response['items']]
                
            channel_details = get_channel_details(channel_ids)
            
            for item in channel_details['items']:
                channel_id = item['id']
                title = item['snippet']['title']
                description = item['snippet']['description']

                print(f"Evaluating channel: {title} ({channel_id})")
                print(f"Description: {description}")

                if channel_id in processed_channels or not is_individual_channel(title, description):
                    print(f"Skipping channel: {title} ({channel_id}) due to filter.")
                    continue                
                
                if matches_category(description, keywords):
                    subscriber_count = int(item['statistics'].get('subscriberCount', 0))
                    video_count = int(item['statistics'].get('videoCount', 0))
                    uploads_playlist_id = item['contentDetails']['relatedPlaylists']['uploads']
                    
                    if MIN_SUBSCRIBERS <= subscriber_count < MAX_SUBSCRIBERS and video_count >= MIN_VIDEOS:
                        language = item['snippet'].get('defaultLanguage', 'en')
                        if language == 'en':
                            total_videos, long_videos = get_video_durations(uploads_playlist_id)
                            
                            if total_videos >= MIN_VIDEOS and long_videos >= MIN_LONG_VIDEOS:
                                # Write channel data to the CSV file
                                writer.writerow([
                                    title,
                                    channel_id,
                                    subscriber_count,
                                    total_videos,
                                    long_videos,
                                    description,
                                    f"https://www.youtube.com/channel/{channel_id}"
                                ])

                                print(f"Added channel: {title} ({channel_id}) with {subscriber_count} subscribers")
                                total_channels_found += 1

                                # Save processed channel ID
                                processed_channels.add(channel_id)
                                with open(processed_channels_file, 'a') as f:
                                    f.write(channel_id + "\n")
                                    
                                if total_channels_found >= OVERALL_CHANNEL_LIMIT:
                                    break
            
            if total_channels_found >= OVERALL_CHANNEL_LIMIT or not response.get('nextPageToken'):
                break
            next_page_token = response.get('nextPageToken')
        
        print(f"Total channels found: {total_channels_found}")

if __name__ == "__main__":
    main()
