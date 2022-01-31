from django.core.management.base import BaseCommand, CommandError

from ...models import UserRegistrationToken

import json

class Command(BaseCommand):
    help = 'Deletes the token and, if any, the user associated with it.'

    def add_arguments(self, parser):
        parser.add_argument('token', type=str)

    def handle(self, *args, **options):
        try:
            token = UserRegistrationToken.objects.get(token=options['token'])
            if token.user is not None:
                token.user.delete()
            token.delete()
            self.stdout.write(json.dumps({'message':'%s deleted.' % options['token']}))
        except UserRegistrationToken.DoesNotExist:
            raise CommandError(json.dumps({'message':'Token "%s" does not exist' % options['token']}))
