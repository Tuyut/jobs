from slacker import Slacker, Error as Sl_Error
from datetime import datetime
CONNECTION_OK = 0
CONNECTION_ERROR = 1
CHANNEL_ERROR = 2

base_token = 'xoxp-19294308839-19294044322-19401435232-79ca3b42fa'

def is_valid_token(token):
    # check connection with token
    # return: Occured error or CONNECTION_OK
    # token: string (slack token)

    sl = Slacker(token)
    try:
        sl.auth.test()
    except Sl_Error as e:
        return e
    return CONNECTION_OK



class SlackAPI:
    
    def __init__(self, token=base_token):
        self.slack = Slacker(token)

        # Dict of existing channels {'name': 'id'}
        self.channels_ids = {}

        # Dict of existing users {'id': 'name'}
        self.users_names = {}

        # Team name
        self.name = None

        # init channels_ids, users_name and name fields
        self.init_team_name() 
        self.get_channels()
        self.get_users()


    def get_name(self):
        return self.name


    def init_team_name(self):
        # Set self.name at team name
        nm = self.slack.team.info()
        self.name = nm.body['team']['name']


    def get_channels(self):
        # Fill self.channels_ids with all existing channels
        # return: CONNECTION_ERROR if can't connect to slack API
        slack_list = self.slack.channels.list()

        if not slack_list.body['ok']:
            return CONNECTION_ERROR

        for chan in slack_list.body['channels']:
            self.channels_ids[chan['name']] = chan['id']
        return CONNECTION_OK
        

    def get_users(self):
        # Fill self.users_ids with all existing users
        # return: CONNECTION_ERROR if can't connect to slack API
        slack_list = self.slack.users.list()

        if not slack_list.body['ok']:
            return CONNECTION_ERROR

        for user in slack_list.body['members']:
            self.users_names[user['id']] = user['name']
        return CONNECTION_OK
    

    def get_channel_id(self, channel_name):
        # Find id for channel_name
        # return: Spread error or CONNECTION_OK
        # channel_name: string
        if channel_name in self.channels_ids.keys():
            return self.channels_ids[channel_name]

        else:
            rl= self.get_channels()

            if rl is not CONNECTION_OK:
                return rl

            if channel_name in self.channels_ids.keys():
                return self.channels_ids[channel_name]

            else:
                return None

    def list_channels(self):
        # List all existing channels
        # return: Spread error or channels list
        rl = self.get_channels()

        if rl is not CONNECTION_OK:
            return rl
        else:
            return sorted(self.channels_ids.keys())

    def parse_messages(self, content):
        # For all messages in content check 
        #   if type is message and there is no subtype
        #   add author and timestamp fields
        # return: list of edited dict
        # content: list of dict

        messages = []
        for mess in content:
            if mess['type'] != 'message':
                continue

            if 'subtype' in mess:
                continue
            
            if 'user' in mess:
                mess['author'] = self.users_names[mess['user']]
            else:
                mess['author'] = 'slack'
            mess['timestamp'] = datetime.fromtimestamp(
                        float(mess['ts'])).strftime('%Y-%m-%d %H:%M:%S')
            messages.append(mess)

        return messages

    def messages_count(self, channel_name):
        # Get the number of messages on a channel
        # return: int 
        # channel_name: string
        chan_id = self.get_channel_id(channel_name)

        if not chan_id:
            return CHANNEL_ERROR
        elif chan_id is CONNECTION_ERROR:
            return chan_id
        else:
            raw_messages = self.slack.channels.history(chan_id)
            if not raw_messages.body['ok']:
                return CONNECTION_ERROR
          
            return len(self.parse_messages(raw_messages.body['messages']))

    def all_messages_count(self):
        # Get the number of messages for all channels
        # return: dict{ string: int }
        count = {}
        channels = self.list_channels()
        
        if isinstance(channels, type(CONNECTION_ERROR)):
            return channels

        for chan in channels:
            count[chan] = self.messages_count(chan)

        return count

    def get_messages(self, channel_name):
        # Get messages on a channel
        # return: list of dict
        # channel_name: string
        chan_id = self.get_channel_id(channel_name)

        if not chan_id:
            return CHANNEL_ERROR
        elif chan_id is CONNECTION_ERROR:
            return chan_id
        else:
            raw_messages = self.slack.channels.history(chan_id)
            if not raw_messages.body['ok']:
                return CONNECTION_ERROR
          
            return self.parse_messages(raw_messages.body['messages'])          

