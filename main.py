import spotify_pull
import compose_story

def main():
    tracks = spotify_pull.get_data()
    compose_story.generate_story(tracks)

if __name__ == "__main__":
    main()