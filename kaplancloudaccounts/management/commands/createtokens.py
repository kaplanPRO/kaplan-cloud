from django.core.management.base import BaseCommand, CommandError

from ...models import UserRegistrationToken

import json

class Command(BaseCommand):
    help = 'Creates and returns tokens for user registration.'

    def add_arguments(self, parser):
        parser.add_argument('n', type=int)

        parser.add_argument(
            '--pm',
            action='store_true',
            help='Indicates that tokens are for pm accounts.'
        )

    def handle(self, *args, **options):
        tokens = {}
        for i in range(options['n']):
            token = UserRegistrationToken()
            if options['pm']:
                token.user_type = 1
            token.save()
            tokens[i] = {'token':token.token, 'type':token.user_type}
        self.stdout.write(json.dumps(tokens))
