#!/usr/bin/env python3
"""
Music Controller
Controls music playback via Mopidy (Snapcast not needed for basic control)
"""

import logging
import random
import requests


class MusicController:
    """Controls music playback through Mopidy"""
    
    def __init__(self, config):
        """Initialize music controller"""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Mopidy settings
        self.mopidy_host = config['mopidy']['host']
        self.mopidy_port = config['mopidy']['port']
        self.mopidy_url = f"http://{self.mopidy_host}:{self.mopidy_port}/mopidy/rpc"
        self.mopidy_timeout = config['mopidy']['timeout']
        
        # Volume settings
        self.volume_step = config['volume']['step']
        self.volume_min = config['volume']['min']
        self.volume_max = config['volume']['max']
        
        # Current state
        self.current_volume = None
        self.muted = False
        self.volume_before_mute = None
        
        # Test Mopidy connection
        self._test_mopidy_connection()
    
    def _test_mopidy_connection(self):
        """Test connection to Mopidy"""
        try:
            result = self._mopidy_request('core.get_version')
            if result:
                self.logger.info(f"Connected to Mopidy (version: {result})")
                return True
            else:
                self.logger.warning("Could not get Mopidy version")
                return False
        except Exception as e:
            self.logger.error(f"Failed to connect to Mopidy: {e}")
            return False
    
    def _mopidy_request(self, method, params=None):
        """
        Send a JSON-RPC request to Mopidy
        
        Args:
            method: Mopidy API method name
            params: Method parameters (optional)
            
        Returns:
            Result from Mopidy, or None on error
        """
        if params is None:
            params = {}
        
        payload = {
            'jsonrpc': '2.0',
            'id': 1,
            'method': method,
            'params': params
        }
        
        try:
            response = requests.post(
                self.mopidy_url,
                json=payload,
                timeout=self.mopidy_timeout
            )
            response.raise_for_status()
            
            result = response.json()
            
            if 'error' in result:
                self.logger.error(f"Mopidy error: {result['error']}")
                return None
            
            return result.get('result')
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Mopidy request failed: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error in Mopidy request: {e}", exc_info=True)
            return None
    
    def search_tracks(self, query):
        """
        Search for tracks in Mopidy
        
        Args:
            query: Search query string
            
        Returns:
            list: List of track URIs
        """
        self.logger.info(f"Searching for: '{query}'")
        
        try:
            # Search in local and TuneIn sources
            search_params = {
                'query': {'any': [query]},
                'uris': ['local:', 'tunein:']
            }
            
            results = self._mopidy_request('core.library.search', search_params)
            
            if not results:
                self.logger.warning("No search results")
                return []
            
            # Extract track URIs from results
            track_uris = []
            for result in results:
                if result and 'tracks' in result:
                    for track in result['tracks']:
                        if 'uri' in track:
                            track_uris.append(track['uri'])
            
            self.logger.info(f"Found {len(track_uris)} tracks")
            return track_uris
            
        except Exception as e:
            self.logger.error(f"Error searching tracks: {e}", exc_info=True)
            return []
    
    def play_random(self, query):
        """
        Search and play a random track
        
        Args:
            query: Search query
            
        Returns:
            bool: True if successful
        """
        track_uris = self.search_tracks(query)
        
        if not track_uris:
            self.logger.warning("No tracks found")
            return False
        
        # Pick a random track
        track_uri = random.choice(track_uris)
        self.logger.info(f"Playing random track: {track_uri}")
        
        # Clear tracklist and add track
        self._mopidy_request('core.tracklist.clear')
        self._mopidy_request('core.tracklist.add', {'uris': [track_uri]})
        
        # Start playback
        return self.play()
    
    def play_playlist(self, query, playlist_num=1):
        """
        Search and play a playlist
        
        Args:
            query: Playlist search query
            playlist_num: Which playlist to play (1-indexed)
            
        Returns:
            bool: True if successful
        """
        self.logger.info(f"Searching for playlist: '{query}' (#{playlist_num})")
        
        try:
            # Get playlists
            playlists = self._mopidy_request('core.playlists.as_list')
            
            if not playlists:
                self.logger.warning("No playlists found")
                return False
            
            # Filter playlists by query
            matching_playlists = [
                p for p in playlists
                if query.lower() in p.get('name', '').lower()
            ]
            
            if not matching_playlists:
                self.logger.warning(f"No playlists matching '{query}'")
                return False
            
            # Get the requested playlist (1-indexed)
            if playlist_num > len(matching_playlists):
                self.logger.warning(
                    f"Playlist #{playlist_num} not found "
                    f"(only {len(matching_playlists)} available)"
                )
                playlist_num = 1
            
            playlist = matching_playlists[playlist_num - 1]
            playlist_uri = playlist.get('uri')
            
            self.logger.info(f"Playing playlist: {playlist.get('name')}")
            
            # Get playlist tracks
            playlist_data = self._mopidy_request(
                'core.playlists.lookup',
                {'uri': playlist_uri}
            )
            
            if not playlist_data or 'tracks' not in playlist_data:
                self.logger.warning("Could not load playlist tracks")
                return False
            
            track_uris = [t['uri'] for t in playlist_data['tracks'] if 'uri' in t]
            
            if not track_uris:
                self.logger.warning("Playlist is empty")
                return False
            
            # Clear tracklist and add playlist tracks
            self._mopidy_request('core.tracklist.clear')
            self._mopidy_request('core.tracklist.add', {'uris': track_uris})
            
            # Start playback
            return self.play()
            
        except Exception as e:
            self.logger.error(f"Error playing playlist: {e}", exc_info=True)
            return False
    
    def play(self):
        """Start playback"""
        result = self._mopidy_request('core.playback.play')
        if result is not None:
            self.logger.info("Playback started")
            return True
        return False
    
    def pause(self):
        """Pause playback"""
        result = self._mopidy_request('core.playback.pause')
        if result is not None:
            self.logger.info("Playback paused")
            return True
        return False
    
    def resume(self):
        """Resume playback"""
        return self.play()
    
    def stop(self):
        """Stop playback"""
        result = self._mopidy_request('core.playback.stop')
        if result is not None:
            self.logger.info("Playback stopped")
            return True
        return False
    
    def next_track(self):
        """Skip to next track"""
        result = self._mopidy_request('core.playback.next')
        if result is not None:
            self.logger.info("Skipped to next track")
            return True
        return False
    
    def previous_track(self):
        """Go to previous track"""
        result = self._mopidy_request('core.playback.previous')
        if result is not None:
            self.logger.info("Went to previous track")
            return True
        return False
    
    def get_current_track(self):
        """
        Get current track information
        
        Returns:
            str: Track information, or None if nothing playing
        """
        track = self._mopidy_request('core.playback.get_current_track')
        
        if not track:
            return None
        
        # Extract track info
        artist = track.get('artists', [{}])[0].get('name', 'Unknown Artist')
        title = track.get('name', 'Unknown Title')
        
        return f"{artist} - {title}"
    
    def set_volume(self, level):
        """
        Set volume to specific level
        
        Args:
            level: Volume level (0-100)
            
        Returns:
            int: New volume level
        """
        level = max(self.volume_min, min(level, self.volume_max))
        
        result = self._mopidy_request('core.mixer.set_volume', {'volume': level})
        
        if result is not None:
            self.current_volume = level
            self.logger.info(f"Volume set to {level}")
            return level
        
        return self.current_volume or 50
    
    def volume_up(self):
        """
        Increase volume
        
        Returns:
            int: New volume level
        """
        current = self._get_volume()
        new_volume = min(current + self.volume_step, self.volume_max)
        return self.set_volume(new_volume)
    
    def volume_down(self):
        """
        Decrease volume
        
        Returns:
            int: New volume level
        """
        current = self._get_volume()
        new_volume = max(current - self.volume_step, self.volume_min)
        return self.set_volume(new_volume)
    
    def _get_volume(self):
        """Get current volume level"""
        if self.current_volume is not None:
            return self.current_volume
        
        volume = self._mopidy_request('core.mixer.get_volume')
        if volume is not None:
            self.current_volume = volume
            return volume
        
        return 50  # Default fallback
    
    def mute(self):
        """Mute audio"""
        if not self.muted:
            self.volume_before_mute = self._get_volume()
            result = self._mopidy_request('core.mixer.set_mute', {'mute': True})
            if result is not None:
                self.muted = True
                self.logger.info("Muted")
                return True
        return False
    
    def unmute(self):
        """Unmute audio"""
        if self.muted:
            result = self._mopidy_request('core.mixer.set_mute', {'mute': False})
            if result is not None:
                self.muted = False
                self.logger.info("Unmuted")
                
                # Restore previous volume if available
                if self.volume_before_mute is not None:
                    self.set_volume(self.volume_before_mute)
                
                return True
        return False
