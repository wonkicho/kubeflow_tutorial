import kfp
from kfp import dsl
from config import get_secret

def preprocess_op():

    return dsl.ContainerOp(
        name='Preprocess Data',
        image='chowk1109/boston_pipeline_preprocessing:latest',
        arguments=[],
        file_outputs={
            'x_train': '/app/x_train.npy',
            'x_test': '/app/x_test.npy',
            'y_train': '/app/y_train.npy',
            'y_test': '/app/y_test.npy',
        }
    )

def train_op(x_train, y_train):

    return dsl.ContainerOp(
        name='Train Model',
        image='chowk1109/boston_pipeline_train:latest',
        arguments=[
            '--x_train', x_train,
            '--y_train', y_train
        ],
        file_outputs={
            'model': '/app/model.pkl'
        }
    )

def test_op(x_test, y_test, model):

    return dsl.ContainerOp(
        name='Test Model',
        image='chowk1109/boston_pipeline_test:latest',
        arguments=[
            '--x_test', x_test,
            '--y_test', y_test,
            '--model', model
        ],
        file_outputs={
            'mean_squared_error': '/app/output.txt',
            'mlpipeline_metrics' : '/app/mlpipeline_metrics.json'
        }
    )



@dsl.pipeline(
   name='Boston Housing Pipeline',
   description='An example pipeline that trains and logs a regression model.'
)
def boston_pipeline():
    _preprocess_op = preprocess_op()
    
    _train_op = train_op(
        dsl.InputArgumentPath(_preprocess_op.outputs['x_train']),
        dsl.InputArgumentPath(_preprocess_op.outputs['y_train'])
    ).after(_preprocess_op)

    _test_op = test_op(
        dsl.InputArgumentPath(_preprocess_op.outputs['x_test']),
        dsl.InputArgumentPath(_preprocess_op.outputs['y_test']),
        dsl.InputArgumentPath(_train_op.outputs['model'])
    ).after(_train_op)

pipeline_package_path = 'my_pipeline.zip'
kfp.compiler.Compiler().compile(boston_pipeline, pipeline_package_path)
client = kfp.Client(host= get_secret("gcp_kubeflow_url"))
client.create_run_from_pipeline_func(boston_pipeline, arguments={})