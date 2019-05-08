from factory import DjangoModelFactory

from ..models import Member


class MemberFactory(DjangoModelFactory):
    class Meta:
        model = Member
