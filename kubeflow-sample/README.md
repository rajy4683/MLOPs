# Kubeflow and PyTorch Lightning
This repo contains few modifications to the CIFAR10 training pipeline in Kubeflow examples. The objective was to explore options provided by PyTorch Lightning. For complete training samples, please refer [this link](https://github.com/kubeflow/pipelines/tree/master/samples/contrib/pytorch-samples). 

The base model used is a ResNet50 which is fine-tuned for CIFAR-10 classes.

Following changes have been made to the pipeline:

1. Introduce a new node called **Overfitting Test** which uses very small batch to train and validate the model prior to executing full training loop. 

   1. This node acts as a gating mechanism and prevents actual training job if the model cannot be overfitted.
   2. To achieve this, a new docker image (based on pytorch-samples/kfp_samples ) was created with the following files:
      1. [cifar10_overfitting.py](https://github.com/rajy4683/MLOPs/blob/master/kubeflow-sample/cifar10/cifar10_overfit.py)
      2. [overfit_component.yaml](https://github.com/rajy4683/MLOPs/blob/master/kubeflow-sample/yaml/overfit_component.yaml)
   3. The pipeline.py was modified to include this new node. 

   ```python
   <     #### Check for overfitting
   <     script_args = f"model_name=resnet.pth"
   <     # For gpus, set number of gpus and accelerator type
   <     ptl_args = "max_epochs=1, gpus=1, accelerator=None, overfit_batches=10"
   <     # pylint: disable=unused-variable
   <     overfit_task = ( # pylint: disable=unused-variable
   <         overfit_op(
   <             input_data=prep_task.outputs["output_data"],
   <             script_args=script_args,
   <             ptl_arguments=ptl_args
   <         ).after(prep_task).set_display_name("Overfitting Test")
   <     )
   ```

2. Modified training mechanism to introduce the following:

   1. Usage of GPU (default example uses CPU)
   2. Enable gradient accumulation strategy to simulate large batch size on limited GPU memory
   3. Enable [Stochastic Weight Averaging](https://pytorch.org/blog/pytorch-1.6-now-includes-stochastic-weight-averaging)
   4. Usage of 16-bit precision during training.
   5. The changes can be found [here](https://github.com/rajy4683/MLOPs/blob/master/kubeflow-sample/cifar10/pipeline.py).

```python
diff --git a/samples/contrib/pytorch-samples/cifar10/pipeline.py b/samples/contrib/pytorch-samples/cifar10/pipeline.py
index 8a64e48be..8aa6ef666 100644
--- a/samples/contrib/pytorch-samples/cifar10/pipeline.py
+++ b/samples/contrib/pytorch-samples/cifar10/pipeline.py
@@ -43,6 +43,7 @@ prepare_tensorboard_op = load_component_from_file(
     "yaml/tensorboard_component.yaml"
 )  # pylint: disable=not-callable
 prep_op = components.load_component_from_file("yaml/preprocess_component.yaml")  # pylint: disable=not-callable
+overfit_op = components.load_component_from_file("yaml/overfit_component.yaml")  # pylint: disable=not-callable
 train_op = components.load_component_from_file("yaml/train_component.yaml")  # pylint: disable=not-callable
 deploy_op = load_component_from_file("yaml/deploy_component.yaml")  # pylint: disable=not-callable
 pred_op = components.load_component_from_file("yaml/prediction_component.yaml")  # pylint: disable=not-callable
@@ -124,17 +125,33 @@ def pytorch_cifar10( # pylint: disable=too-many-arguments
         prep_op().after(prepare_tb_task
                        ).set_display_name("Preprocess & Transform")
     )
+
+    #### Check for overfitting
+    script_args = f"model_name=resnet.pth"
+    # For gpus, set number of gpus and accelerator type
+    ptl_args = "max_epochs=1, gpus=0, accelerator=None, overfit_batches=10"
+    # pylint: disable=unused-variable
+    overfit_task = ( # pylint: disable=unused-variable
+        overfit_op(
+            input_data=prep_task.outputs["output_data"],
+            script_args=script_args,
+            ptl_arguments=ptl_args
+        ).after(prep_task).set_display_name("Overfitting Test")
+    )
+
+
     confusion_matrix_url = f"minio://{log_bucket}/{confusion_matrix_log_dir}"
+
     script_args = f"model_name=resnet.pth," \
                   f"confusion_matrix_url={confusion_matrix_url}"
     # For gpus, set number of gpus and accelerator type
-    ptl_args = "max_epochs=1, gpus=0, accelerator=None, profiler=pytorch"
+    ptl_args = "max_epochs=1, gpus=1, accelerator=None, profiler=pytorch, precision=16, accumulate_grad_batches=1, stochastic_weight_avg=True"
     train_task = (
         train_op(
             input_data=prep_task.outputs["output_data"],
             script_args=script_args,
             ptl_arguments=ptl_args
-        ).after(prep_task).set_display_name("Training")
+        ).after(overfit_task).set_display_name("Training")
     )
     # For GPU uncomment below line and set GPU limit and node selector
     # ).set_gpu_limit(1).add_node_selector_constraint
```

### Sample workflow graph

![Workflow Graph](https://github.com/rajy4683/MLOPs/blob/master/kubeflow-sample/imgs/SuccessfulExpCust.JPG)



