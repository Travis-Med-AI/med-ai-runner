# coding: utf-8
from sqlalchemy import BigInteger, Boolean, Column, ForeignKey, Integer, String, Table, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata


class AppSetting(Base):
    __tablename__ = 'app_settings'

    id = Column(Integer, primary_key=True, server_default=text("nextval('app_settings_id_seq'::regclass)"))
    orthancUrl = Column(String)
    rabbitmqUrl = Column(String)
    redisUrl = Column(String)
    lastUpdate = Column(TIMESTAMP(precision=3), nullable=False, server_default=text("('now'::text)::timestamp(3) with time zone"))


class Migration(Base):
    __tablename__ = 'migrations'

    id = Column(Integer, primary_key=True, server_default=text("nextval('migrations_id_seq'::regclass)"))
    timestamp = Column(BigInteger, nullable=False)
    name = Column(String, nullable=False)


class Role(Base):
    __tablename__ = 'role'

    id = Column(Integer, primary_key=True, server_default=text("nextval('role_id_seq'::regclass)"))
    name = Column(String, nullable=False)
    description = Column(String)

    user = relationship('User', secondary='user_roles_role')


class Study(Base):
    __tablename__ = 'study'

    id = Column(Integer, primary_key=True, server_default=text("nextval('study_id_seq'::regclass)"))
    orthancStudyId = Column(String, nullable=False, unique=True)
    orthancParentId = Column(String)
    patientId = Column(String)
    studyUid = Column(String)
    accession = Column(String)
    seriesUid = Column(String)
    type = Column(Text)
    modality = Column(String)
    description = Column(String)
    seriesMetadata = Column(JSONB(astext_type=Text()))
    studyMetadata = Column(JSONB(astext_type=Text()))
    failed = Column(Boolean, nullable=False, server_default=text("false"))
    deletedFromOrthanc = Column(Boolean, nullable=False, server_default=text("false"))
    dateAdded = Column(BigInteger, nullable=False)
    lastUpdate = Column(TIMESTAMP(precision=3), nullable=False, server_default=text("('now'::text)::timestamp(3) with time zone"))


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, server_default=text("nextval('user_id_seq'::regclass)"))
    email = Column(String, nullable=False)
    firstName = Column(String, nullable=False)
    lastName = Column(String, nullable=False)
    password = Column(String, nullable=False)
    salt = Column(String, nullable=False)


class Model(Base):
    __tablename__ = 'model'

    id = Column(Integer, primary_key=True, server_default=text("nextval('model_id_seq'::regclass)"))
    image = Column(String, nullable=False, unique=True)
    displayName = Column(String, nullable=False, unique=True)
    input = Column(String, nullable=False)
    modality = Column(String, nullable=False)
    inputType = Column(String)
    output = Column(String, nullable=False)
    outputKeys = Column(JSONB(astext_type=Text()))
    hasImageOutput = Column(Boolean, nullable=False)
    pulled = Column(Boolean, nullable=False, server_default=text("false"))
    failedPull = Column(Boolean, nullable=False, server_default=text("false"))
    concurrency = Column(Integer, nullable=False, server_default=text("1"))



class Notification(Base):
    __tablename__ = 'notification'

    id = Column(Integer, primary_key=True, server_default=text("nextval('notification_id_seq'::regclass)"))
    type = Column(String, nullable=False)
    message = Column(String, nullable=False)
    read = Column(Boolean, nullable=False)
    userId = Column(ForeignKey('user.id', ondelete='CASCADE', onupdate='CASCADE'))

    user = relationship('User')


t_user_roles_role = Table(
    'user_roles_role', metadata,
    Column('userId', ForeignKey('user.id', ondelete='CASCADE'), primary_key=True, nullable=False, index=True),
    Column('roleId', ForeignKey('role.id', ondelete='CASCADE'), primary_key=True, nullable=False, index=True)
)


class Classifier(Base):
    __tablename__ = 'classifier'

    id = Column(Integer, primary_key=True, server_default=text("nextval('classifier_id_seq'::regclass)"))
    modality = Column(String, nullable=False, unique=True)
    modelId = Column(ForeignKey('model.id'))

    model = relationship('Model')


class EvalJob(Base):
    __tablename__ = 'eval_job'

    id = Column(Integer, primary_key=True, server_default=text("nextval('eval_job_id_seq'::regclass)"))
    batchSize = Column(Integer, nullable=False, server_default=text("1"))
    running = Column(Boolean, nullable=False)
    cpu = Column(Boolean, nullable=False, server_default=text("false"))
    deleteOrthanc = Column(Boolean, nullable=False, server_default=text("false"))
    replicas = Column(Integer, nullable=False, server_default=text("0"))
    modelId = Column(ForeignKey('model.id', ondelete='CASCADE'), unique=True)

    model = relationship('Model', uselist=False)


class Experiment(Base):
    __tablename__ = 'experiment'

    id = Column(Integer, primary_key=True, server_default=text("nextval('experiment_id_seq'::regclass)"))
    name = Column(String, nullable=False, unique=True)
    type = Column(Text, nullable=False)
    status = Column(Text, nullable=False, server_default=text("'NEW'::text"))
    createdDate = Column(TIMESTAMP(precision=3), nullable=False, server_default=text("('now'::text)::timestamp(3) with time zone"))
    lastUpdate = Column(TIMESTAMP(precision=3), nullable=False, server_default=text("('now'::text)::timestamp(3) with time zone"))
    modelId = Column(ForeignKey('model.id'))
    userId = Column(ForeignKey('user.id'))

    model = relationship('Model')
    user = relationship('User')
    study = relationship('Study', secondary='experiment_studies_study')


class ModelTrain(Base):
    __tablename__ = 'model_train'

    id = Column(Integer, primary_key=True, server_default=text("nextval('model_train_id_seq'::regclass)"))
    failed = Column(Boolean, nullable=False, server_default=text("false"))
    modelId = Column(ForeignKey('model.id', ondelete='CASCADE'), unique=True)
    training = Column(Boolean, nullable=False, server_default=text("false"))
    modelOutput = Column(JSONB(astext_type=Text()))
    studyId = Column(ForeignKey('study.id', ondelete='CASCADE'), unique=True)

    model = relationship('Model', uselist=False)
    study = relationship('Study', uselist=False)


class StudyEvaluation(Base):
    __tablename__ = 'study_evaluation'
    __table_args__ = (
        UniqueConstraint('modelId', 'studyId'),
    )

    id = Column(Integer, primary_key=True, server_default=text("nextval('study_evaluation_id_seq'::regclass)"))
    modelOutput = Column(JSONB(astext_type=Text()))
    stdout = Column(JSONB(astext_type=Text()))
    status = Column(String, nullable=False)
    imgOutputPath = Column(String)
    lastUpdate = Column(TIMESTAMP(precision=3), nullable=False, server_default=text("('now'::text)::timestamp(3) with time zone"))
    studyId = Column(ForeignKey('study.id'))
    modelId = Column(ForeignKey('model.id', ondelete='CASCADE'))
    finishTime = Column(Integer)
    startTime = Column(Integer)

    model = relationship('Model')
    study = relationship('Study')


class StudyLabel(Base):
    __tablename__ = 'study_label'

    id = Column(Integer, primary_key=True, server_default=text("nextval('study_label_id_seq'::regclass)"))
    label = Column(JSONB(astext_type=Text()), nullable=False)
    studyId = Column(ForeignKey('study.id'))
    modelId = Column(ForeignKey('model.id', ondelete='CASCADE', onupdate='CASCADE'))

    model = relationship('Model')
    study = relationship('Study')


t_experiment_studies_study = Table(
    'experiment_studies_study', metadata,
    Column('experimentId', ForeignKey('experiment.id', ondelete='CASCADE'), primary_key=True, nullable=False, index=True),
    Column('studyId', ForeignKey('study.id', ondelete='CASCADE'), primary_key=True, nullable=False, index=True)
)
