"""Default user model implementations..

.. note ::

    Horus dependencies will be killed in the future. Do not rely on them.

"""
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.declarative.base import _declarative_constructor

from hem.text import pluralize
from horus import models as horus_models
from websauna.system.user.interfaces import IGroup, IUser
from websauna.system.user.usermixin import ActivationMixin
from zope.interface import implementer

from . import usermixin


@implementer(IUser)
class User(usermixin.UserMixin, horus_models.UserMixin):
    """The default user implementation for Websauna.

    This is a concrete implementation of SQLAlchemy model.
    """

    # In PSQL "user", the automatically generated table name, is a reserved word
    __tablename__ = "users"

    __init__ = _declarative_constructor

    @property
    def last_login_date(self):
        # Our internal declaration which matches Horus way of saying the same thing
        # TODO: Remove Horus as a dependency
        return self.last_login_at

    # Fix SAWarning: Unmanaged access of declarative attribute __tablename__ from non-mapped class ...
    # Apparently one cannot refer to attributes from mixin classes.
    @declared_attr
    def activation_id(self):
        return sa.Column(
            sa.Integer,
            sa.ForeignKey('%s.%s' % (
                    Activation.__tablename__,
                    self._idAttribute
                )
            )
        )


@implementer(IGroup)
class Group(usermixin.GroupMixin, horus_models.GroupMixin):

    __init__ = _declarative_constructor

    # Fix SAWarning: Unmanaged access of declarative attribute __tablename__ from non-mapped class ...
    @declared_attr
    def users(self):
        """Relationship for users belonging to this group"""
        return sa.orm.relationship(
            'User',
            secondary=UserGroup.__tablename__,
            # order_by='%s.user.username' % UserMixin.__tablename__,
            passive_deletes=True,
            passive_updates=True,
            backref=pluralize(Group.__tablename__),
        )



class UserGroup(horus_models.UserGroupMixin):
    """Map one user to one group."""

    __tablename__ = "usergroup"

    # Default constructor
    __init__ = _declarative_constructor

    @declared_attr
    def user_id(self):

        # Fix table name for User table, Horus bugs out PSQL
        return sa.Column(
            sa.Integer,
            sa.ForeignKey('%s.%s' % (User.__tablename__,
                                     self._idAttribute),
                          onupdate='CASCADE',
                          ondelete='CASCADE'),
        )

    # Fix SAWarning: Unmanaged access of declarative attribute __tablename__ from non-mapped class ...
    @declared_attr
    def group_id(self):
        return sa.Column(
            sa.Integer,
            sa.ForeignKey('%s.%s' % (
                Group.__tablename__,
                self._idAttribute)
            )
        )


class Activation(ActivationMixin, horus_models.ActivationMixin):
    """The default implementation of user email activation token."""

    __tablename__ = "user_activation"

    # Default constructor
    __init__ = _declarative_constructor




