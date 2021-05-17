from pyzoom_oauth import Zoom

zoom = Zoom(
    client_id='',  # Your apps client id
    client_secret='',  # Your apps client secret
    oauth_redirect_uri='http://localhost:8080/zoom_login'  # Your apps redirect url
)

print(f'Open {zoom.get_oauth_url()} in your browser and give access')
uri = input("Paste url that you got redirected to into here: ")
zoom.oauth_receiver(uri)
recordings = zoom.get_recordings()

if recordings:
    for f in recordings[0].recording_files:
        f.save("./test_download")
    # Same as recordings[0].save("./test_download")
pass

