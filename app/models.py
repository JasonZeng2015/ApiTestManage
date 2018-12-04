# encoding: utf-8
from werkzeug.security import check_password_hash, generate_password_hash
from . import db, login_manager
import datetime
from flask_login import UserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app


roles_permissions = db.Table('roles_permissions',
                             db.Column('role_id', db.Integer, db.ForeignKey('role.id')),
                             db.Column('permission_id', db.Integer, db.ForeignKey('permission.id')))


class Role(db.Model):
    __tablename__ = 'role'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True)
    users = db.relationship('User', back_populates='role')
    permission = db.relationship('Permission', secondary=roles_permissions, back_populates='role')

    @staticmethod
    def init_role():
        roles_permissions_map = {'测试人员': ['COMMON'],
                                 '管理员': ['COMMON', 'ADMINISTER']}
        for role_name in roles_permissions_map:
            role = Role.query.filter_by(name=role_name).first()
            if role is None:
                role = Role(name=role_name)
                db.session.add(role)
                role.permission = []
            for permission_name in roles_permissions_map[role_name]:
                permission = Permission.query.filter_by(name=permission_name).first()
                if permission is None:
                    permission = Permission(name=permission_name)
                    db.session.add(permission)
                role.permission.append(permission)
                db.session.commit()
        print('Role and permission created successfully')


class Permission(db.Model):
    __tablename__ = 'permission'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True)
    role = db.relationship('Role', secondary=roles_permissions, back_populates='permission')


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    account = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    name = db.Column(db.String(64))
    status = db.Column(db.Integer)
    created_time = db.Column(db.DateTime, index=True, default=datetime.datetime.utcnow)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    role = db.relationship('Role', back_populates='users')

    @staticmethod
    def init_user():
        user = User.query.filter_by(name='管理员').first()
        if user:
            print('The administrator account already exists')
            print('--' * 30)
            return
        else:
            user = User(name='管理员', account='admin', password='123456', status=1,role_id=2)
            db.session.add(user)
            db.session.commit()
            print('Administrator account created successfully')
            print('--'*30)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_reset_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id})

    def can(self, permission_name):
        permission = Permission.query.filter_by(name=permission_name).first()
        return permission is not None and self.role is not None and permission in self.role.permission


class Project(db.Model):
    __tablename__ = 'project'
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), nullable=True)
    name = db.Column(db.String(), nullable=True, unique=True)
    host = db.Column(db.String(), nullable=True)
    host_two = db.Column(db.String())
    host_three = db.Column(db.String())
    host_four = db.Column(db.String())
    environment_choice = db.Column(db.String())
    principal = db.Column(db.String(), nullable=True)
    variables = db.Column(db.String())
    headers = db.Column(db.String())
    created_time = db.Column(db.DateTime, index=True, default=datetime.datetime.utcnow)
    modules = db.relationship('Module', order_by='Module.num.asc()', lazy='dynamic')
    configs = db.relationship('Config', order_by='Config.num.asc()', lazy='dynamic')
    case_sets = db.relationship('CaseSet', order_by='CaseSet.num.asc()', lazy='dynamic')


class Module(db.Model):
    __tablename__ = 'module'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(), nullable=True)
    num = db.Column(db.Integer(), nullable=True)
    created_time = db.Column(db.DateTime, index=True, default=datetime.datetime.utcnow)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    api_msg = db.relationship('ApiMsg', order_by='ApiMsg.num.asc()', lazy='dynamic')


class Config(db.Model):
    __tablename__ = 'config'
    id = db.Column(db.Integer(), primary_key=True)
    num = db.Column(db.Integer(), nullable=True)
    name = db.Column(db.String())
    variables = db.Column(db.String())
    func_address = db.Column(db.String())
    created_time = db.Column(db.DateTime, index=True, default=datetime.datetime.utcnow)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))


class CaseSet(db.Model):
    __tablename__ = 'case_set'
    id = db.Column(db.Integer(), primary_key=True)
    num = db.Column(db.Integer(), nullable=True)
    name = db.Column(db.String(), nullable=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.datetime.utcnow)
    created_time = db.Column(db.DateTime, index=True, default=datetime.datetime.utcnow)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    cases = db.relationship('Case', order_by='Case.num.asc()', lazy='dynamic')


class Case(db.Model):
    __tablename__ = 'case'
    id = db.Column(db.Integer(), primary_key=True)
    num = db.Column(db.Integer(), nullable=True)
    name = db.Column(db.String(), nullable=True)
    desc = db.Column(db.String())
    func_address = db.Column(db.String())
    variable = db.Column(db.String())
    times = db.Column(db.Integer(), nullable=True)
    created_time = db.Column(db.DateTime, index=True, default=datetime.datetime.utcnow)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    case_set_id = db.Column(db.Integer, db.ForeignKey('case_set.id'))


class ApiMsg(db.Model):
    __tablename__ = 'api_msg'
    id = db.Column(db.Integer(), primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.datetime.utcnow)
    num = db.Column(db.Integer(), nullable=True)
    name = db.Column(db.String(), nullable=True)
    desc = db.Column(db.String(), nullable=True)
    variable_type = db.Column(db.String(), nullable=True)
    status_url = db.Column(db.String(), nullable=True)
    func_address = db.Column(db.String())
    up_func = db.Column(db.String())
    down_func = db.Column(db.String())
    method = db.Column(db.String(), nullable=True)
    variable = db.Column(db.String())
    json_variable = db.Column(db.String())
    param = db.Column(db.String())
    url = db.Column(db.String(), nullable=True)
    extract = db.Column(db.String())
    validate = db.Column(db.String())
    header = db.Column(db.String())
    module_id = db.Column(db.Integer, db.ForeignKey('module.id'))
    project_id = db.Column(db.Integer, nullable=True)


class ApiSuite(db.Model):
    __tablename__ = 'apiSuite'
    id = db.Column(db.Integer(), primary_key=True)
    create_time = db.Column(db.DateTime, index=True, default=datetime.datetime.utcnow)
    update_time = db.Column(db.DateTime, index=True, default=datetime.datetime.utcnow)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.datetime.utcnow)
    num = db.Column(db.Integer(), nullable=True)
    name = db.Column(db.String(), nullable=True)
    api_ids = db.Column(db.String(), nullable=True)
    module_id = db.Column(db.Integer, db.ForeignKey('module.id'))


class CaseData(db.Model):
    __tablename__ = 'case_data'
    id = db.Column(db.Integer(), primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.datetime.utcnow)
    num = db.Column(db.Integer(), nullable=True)
    status = db.Column(db.String())
    name = db.Column(db.String())
    up_func = db.Column(db.String())
    down_func = db.Column(db.String())
    time = db.Column(db.Integer(), default=1)
    param = db.Column(db.String(), default=u'[]')
    status_param = db.Column(db.String, default=u'[true, true]')
    variable = db.Column(db.String())
    json_variable = db.Column(db.String())
    status_variables = db.Column(db.String)
    extract = db.Column(db.String())
    status_extract = db.Column(db.String)
    validate = db.Column(db.String())
    status_validate = db.Column(db.String)
    case_id = db.Column(db.Integer, db.ForeignKey('case.id'))
    api_msg_id = db.Column(db.Integer, db.ForeignKey('api_msg.id'))


class Report(db.Model):
    __tablename__ = 'report'
    id = db.Column(db.Integer(), primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.datetime.utcnow)
    name = db.Column(db.String(), nullable=True)
    belong_pro = db.Column(db.String(), nullable=True)
    read_status = db.Column(db.String, nullable=True)
    data = db.Column(db.String(65500), nullable=True)


class Task(db.Model):  # 定时任务的
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    num = db.Column(db.Integer())
    task_name = db.Column(db.String(52))  # 任务名称
    task_config_time = db.Column(db.String(252), nullable=True)  # 任务执行时间
    timestamp = db.Column(db.DateTime(), default=datetime.datetime.now())  # 任务的创建时间
    project_name = db.Column(db.String(), nullable=True)
    set_id = db.Column(db.String())
    case_id = db.Column(db.String())
    task_type = db.Column(db.String())
    task_to_email_address = db.Column(db.String(252))  # 收件人邮箱
    task_send_email_address = db.Column(db.String(252))  # 维护本计划的人的邮箱
    email_password = db.Column(db.String())
    status = db.Column(db.String(), default=u'创建')  # 任务的运行状态，默认是创建


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
