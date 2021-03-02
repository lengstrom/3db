import torch as ch

class Evaluator:
    def __init__(self): pass

    def is_correct(self, pred, label): raise NotImplementedError

    def loss(self, pred, label): raise NotImplementedError

    def extra_info(self, pred, label): pass

    def to_tensor(self, pred, output_shape, input_shape): 
        if isinstance(pred, ch.Tensor):
            assert list(pred.shape) == list(output_shape), \
                f"Shape of prediction ({pred.shape.item()}) does not match declared shape ({output_shape})"
            return pred
        ERR_MSG = "Must implement evaluator.to_tensor if prediction is not already a tensor"
        raise ValueError(ERR_MSG)
