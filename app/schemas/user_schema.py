from marshmallow import Schema, fields, EXCLUDE


class UserSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    email = fields.Email(required=True)
    password = fields.Str(required=True)
    description = fields.Str(required=False)
