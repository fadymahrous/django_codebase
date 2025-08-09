from rest_framework import serializers

from .models import User

class UserSerializer(serializers.Serializer):
    id= serializers.IntegerField(read_only=True)
    username = serializers.CharField(max_length=150)
    first_name = serializers.CharField(max_length=30, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    birthdate = serializers.DateField(required=False, allow_null=True)
    nationalid = serializers.IntegerField(required=False, allow_null=True)
    phonenumber = serializers.CharField(max_length=20)
    wallet = serializers.DecimalField(max_digits=12, decimal_places=2, required=False,)

    def create(self, validated_data):
        return User.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.username = validated_data.get('username', instance.username)
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.email = validated_data.get('email', instance.email)
        instance.birthdate = validated_data.get('birthdate', instance.birthdate)
        instance.nationalid = validated_data.get('nationalid', instance.nationalid)
        instance.phonenumber = validated_data.get('phonenumber', instance.phonenumber)
        instance.wallet = validated_data.get('wallet', instance.wallet)
        instance.save()
        return instance
    
    def delete(self,instance):
        return User.delete(instance)