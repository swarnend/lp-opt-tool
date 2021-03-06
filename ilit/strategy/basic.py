import copy
from collections import OrderedDict
import itertools
from .strategy import strategy_registry, TuneStrategy
from ..utils import logger


@strategy_registry
class BasicTuneStrategy(TuneStrategy):
    """The basic tuning strategy which tunes the low precision model with below order.

    1. modelwise tuning for all quantizable ops.
    2. fallback tuning from bottom to top to decide the priority of which op has biggest impact on accuracy.
    3. incremental fallback tuning by fallbacking multiple ops with the order got from #2.

    Args:
        model (object):                        The FP32 model specified for low precision tuning.
        conf (Class):                          The Conf class instance initialized from user yaml config file.
        q_dataloader (generator):              Data loader for calibration, mandatory for post-training quantization.
                                               It is iterable and should yield a tuple (input, label) for calibration
                                               dataset containing label, or yield (input, _) for label-free calibration
                                               dataset. The input could be a object, list, tuple or dict, depending on
                                               user implementation, as well as it can be taken as model input.
        q_func (function, optional):           Reserved for future use.
        eval_dataloader (generator, optional): Data loader for evaluation. It is iterable and should yield a tuple
                                               of (input, label). The input could be a object, list, tuple or dict,
                                               depending on user implementation, as well as it can be taken as model
                                               input. The label should be able to take as input of supported
                                               metrics. If this parameter is not None, user needs to specify
                                               pre-defined evaluation metrics through configuration file and should
                                               set "eval_func" paramter as None. Tuner will combine model,
                                               eval_dataloader and pre-defined metrics to run evaluation process.
        eval_func (function, optional):        The evaluation function provided by user. This function takes model
                                               as parameter, and evaluation dataset and metrics should be encapsulated
                                               in this function implementation and outputs a higher-is-better accuracy
                                               scalar value.

                                               The pseudo code should be something like:

                                               def eval_func(model):
                                                    input, label = dataloader()
                                                    output = model(input)
                                                    accuracy = metric(output, label)
                                                    return accuracy
        dicts (dict, optional):                The dict containing resume information. Defaults to None.

    """

    def __init__(self, model, conf, q_dataloader, q_func=None,
                 eval_dataloader=None, eval_func=None, dicts=None):
        super(
            BasicTuneStrategy,
            self).__init__(
            model,
            conf,
            q_dataloader,
            q_func,
            eval_dataloader,
            eval_func,
            dicts)

    def next_tune_cfg(self):
        """The generator of yielding next tuning config to traverse by concrete strategies
           according to last tuning result.

        """
        # Model wise tuning
        op_cfgs = {}
        best_cfg = None
        best_acc = 0

        logger.debug('Start basic strategy by model-wise tuning')
        for iterations in self.calib_iter:
            op_cfgs['calib_iteration'] = int(iterations)
            for tune_cfg in self.modelwise_quant_cfgs:
                op_cfgs['op'] = OrderedDict()

                for op in self.opwise_quant_cfgs:
                    op_cfg = copy.deepcopy(self.opwise_quant_cfgs[op])
                    if len(op_cfg) > 0:
                        if tune_cfg not in op_cfg:
                            op_cfgs['op'][op] = copy.deepcopy(op_cfg[0])
                        else:
                            op_cfgs['op'][op] = copy.deepcopy(tune_cfg)
                    else:
                        op_cfgs['op'][op] = copy.deepcopy(
                            self.opwise_tune_cfgs[op][0])

                yield op_cfgs
                acc, _ = self.last_tune_result
                if acc >= best_acc:
                    best_acc = acc
                    best_cfg = copy.deepcopy(op_cfgs)

        if best_cfg is None:
            return
        
        fallback_dtypes = []
        for data_type in ["bf16", "fp32"]:
            if data_type in self.modelwise_tune_space["activation"]["dtype"]:
                fallback_dtypes.append(data_type)

        for fallback_dtype in fallback_dtypes:
            logger.debug('Continue basic strategy by sorting opwise %s fallback priority' % (fallback_dtype))
            ops_acc = OrderedDict()
            for op, configs in reversed(self.opwise_tune_cfgs.items()):
                op_cfgs = copy.deepcopy(best_cfg)
                for cfg in configs:
                    if fallback_dtype == cfg['activation']['dtype']:
                        op_cfgs['op'][op]['activation'].clear()
                        op_cfgs['op'][op]['activation']['dtype'] = fallback_dtype
                        if 'weight' in cfg:
                            assert cfg['weight']['dtype'] == fallback_dtype
                            op_cfgs['op'][op]['weight'].clear()
                            op_cfgs['op'][op]['weight']['dtype'] = fallback_dtype
                yield op_cfgs
                acc, _ = self.last_tune_result
                ops_acc[op] = acc

            logger.debug('Continue basic strategy by incremental opwise %s fallback with priority' % (fallback_dtype))
            op_cfgs = copy.deepcopy(best_cfg)
            if ops_acc is not None:
                ordered_ops = sorted(ops_acc.keys(), key=lambda key: ops_acc[key], reverse=True)
                for op in ordered_ops:
                    old_cfg = copy.deepcopy(op_cfgs['op'][op])
                    op_cfgs['op'][op]['activation'].clear()
                    op_cfgs['op'][op]['activation']['dtype'] = fallback_dtype
                    if 'weight' in op_cfgs['op'][op]:
                        op_cfgs['op'][op]['weight'].clear()
                        op_cfgs['op'][op]['weight']['dtype'] = fallback_dtype
                    yield op_cfgs
                    acc, _ = self.last_tune_result
                    if acc <= best_acc:
                        op_cfgs['op'][op] = copy.deepcopy(old_cfg)
                    else:
                        best_acc = acc

                op_cfgs = copy.deepcopy(best_cfg)
                for op in ordered_ops:
                    op_cfgs['op'][op]['activation'].clear()
                    op_cfgs['op'][op]['activation']['dtype'] = fallback_dtype
                    if 'weight' in op_cfgs['op'][op]:
                        op_cfgs['op'][op]['weight'].clear()
                        op_cfgs['op'][op]['weight']['dtype'] = fallback_dtype
                    yield op_cfgs

        return
