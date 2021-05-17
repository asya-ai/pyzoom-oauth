# pyzoom-oauth

Simple code fragment to access zoom api via OAuth

### Right now implemented endpoints are:
* Auth
  * Get token
  * Refresh token
* Recordings
  * Get recordings (Due to zoom api restrictions, only recordings made within last month are available)
  * Download recording

### To use this:
* you need to create zoom application here: https://marketplace.zoom.us -> Develop -> View App Types -> OAuth

* copy [pyzoom_oauth.py](pyzoom_oauth.py) into your directory structure and see [example.py](example.py) how to use it
