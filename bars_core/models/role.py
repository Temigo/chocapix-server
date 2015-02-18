from django.db import models
from rest_framework import viewsets
from rest_framework import serializers, decorators
from rest_framework.response import Response

from bars_django.utils import VirtualField
from bars_core.models.bar import Bar
from bars_core.models.user import User


role_map = {}
role_map['customer'] = [
    'bars_transactions.add_transaction',
    'bars_transactions.add_buytransaction',
    'bars_transactions.add_throwtransaction',
    'bars_transactions.add_givetransaction',
    'bars_transactions.add_mealtransaction',
]
role_map['newsmanager'] = [
    'bars_news.add_news',
    'bars_news.change_news',
    'bars_news.delete_news',
]
role_map['appromanager'] = [
    'bars_transactions.add_transaction',
    'bars_transactions.add_approtransaction',
    'bars_base.add_item',
    'bars_base.change_item',
    # 'bars_base.delete_item',
]
role_map['inventorymanager'] = role_map['appromanager'] + [
    'bars_transactions.add_transaction',
    'bars_transactions.add_inventorytransaction',
]
role_map['staff'] = role_map['inventorymanager'] + [
    'bars_transactions.add_transaction',
    'bars_transactions.add_deposittransaction',
    'bars_transactions.add_punishtransaction',
    'bars_transactions.change_transaction',
]
role_map['admin'] = role_map['staff'] + role_map['newsmanager'] + [
    'bars_core.add_role',
    'bars_core.change_role',
    'bars_core.delete_role',
    'bars_base.add_account',
    'bars_base.change_account',
    'bars_base.delete_account',
]
role_list = list(role_map.keys())


class Role(models.Model):
    class Meta:
        app_label = 'bars_core'
    name = models.CharField(max_length=127, choices=zip(role_list, role_list))
    bar = models.ForeignKey(Bar)
    user = models.ForeignKey(User)
    last_modified = models.DateTimeField(auto_now=True)

    def get_permissions(self):
        return role_map[self.name] if self.name in role_map else []

    def __unicode__(self):
        return self.user.username + " : " + self.name + " (" + self.bar.id + ")"


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
    _type = VirtualField("Role")
    perms = serializers.ListField(child=serializers.CharField(max_length=127), read_only=True, source='get_permissions')


from bars_core.perms import PerBarPermissionsOrAnonReadOnly

class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = (PerBarPermissionsOrAnonReadOnly,)
    filter_fields = {
        'user': ['exact'],
        'bar': ['exact'],
        'name': ['exact']}

    @decorators.list_route(methods=['get'])
    def me(self, request):
        bar = request.QUERY_PARAMS.get('bar', None)
        if bar is None:
            roles = request.user.role_set.all()
        else:
            roles = request.user.role_set.filter(bar=bar)
        serializer = self.serializer_class(roles)
        return Response(serializer.data)