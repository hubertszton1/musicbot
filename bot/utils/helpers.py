def format_song_info(title, artist, duration):
    return f"{title} by {artist} - Duration: {duration}"

def manage_queue(queue, action, song=None):
    if action == "add" and song:
        queue.append(song)
    elif action == "remove" and song in queue:
        queue.remove(song)
    return queue

def clear_queue(queue):
    queue.clear()
    return queue

def is_valid_url(url):
    # Simple check for a valid URL format
    return url.startswith("http://") or url.startswith("https://")