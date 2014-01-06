"""Random Forest classifier using R's randomForest library.
RPy2 is used to interface with R."""
import rpy2.robjects as ro
import pandas.rpy.common as com
import pandas as pd
from generic_classifier import GenericClassifier
import features.python.features as features
import logging


class MyClassifier(object):
    """
    The MyClassifier class is intended to only be used by RRandomForest.
    Essentially MyClassifier is a wrapper around R's randomForest libary,
    to make it compatible with the methods used by scikit learn (predict,
    fit, predic_proba). The advantage of R's version of random forest is
    that it allows the sampling rate to be specified.
    """

    def __init__(self,
                 ntree=1000,
                 other_sample=.02,
                 driver_sample=.7):
        self.ntree = ntree
        self.other_sample_rate = other_sample
        self.driver_sample_rate = driver_sample

        # Code for R's random forest using rpy2
        ro.r("library(randomForest)")  # load randomForest library

        # R function for fitting a random forest
        ro.r('''rf_fit <- function(df, ntree, sampSize){
                df$true_class <- as.factor(df$true_class)
                rf <- randomForest(true_class~.,
                                   data=df,
                                   replace=TRUE,
                                   ntree=ntree,
                                   classwt=1/sampSize,
                                   sampsize=sampSize)
                return(rf)
             }''')
        self.rf_fit = ro.r['rf_fit']

        # R function for predicting class probability
        ro.r('''rf_pred_prob <- function(rf, xtest){
                prob <- predict(rf, xtest, type="prob")
                return(prob)
             }''')
        self.rf_pred_prob = ro.r['rf_pred_prob']

        # R function for predicting class
        ro.r('''rf_pred <- function(rf, xtest){
                prob <- predict(rf, xtest)
                return(prob)
             }''')
        self.rf_pred = ro.r['rf_pred']

    def set_sample_size(self, sampsize):
        sampsize[0] *= self.other_sample_rate
        sampsize[1] *= self.driver_sample_rate
        sampsize[2] *= self.driver_sample_rate
        self.sample_size = ro.IntVector(sampsize)

    def fit(self, xtrain, ytrain):
        """The fit method trains R's random forest classifier.

        NOTE: the method name ("fit") and method signature were choosen
        to be consistent with scikit learn's fit method.

        **Parameters**

        xtrain : pd.DataFrame
            features for training set
        ytrain : pd.DataFrame
            true class labels (as integers) for training set
        """
        label_counts = ytrain.value_counts()
        sampsize = [label_counts[self.other_num],
                    label_counts[self.onco_num],
                    label_counts[self.tsg_num]]
        self.set_sample_size(sampsize)
        xtrain['true_class'] = ytrain
        r_xtrain = com.convert_to_r_dataframe(xtrain)
        self.rf = self.rf_fit(r_xtrain, self.ntree, self.sample_size)

    def set_classes(self, oncogene, tsg):
        """Sets the integers used to represent classes in classification."""
        if not oncogene and not tsg:
            raise ValueError('Classification needs at least two classes')
        elif oncogene and tsg:
            self.other_num = 0
            self.onco_num = 1
            self.tsg_num = 2
            self.num_classes = 3
        else:
            self.other_num = 0
            self.num_classes = 2
            self.onco_num = 1 if oncogene else 0
            self.tsg_num = 1 if tsg else 0

    def predict(self, xtest):
        """Predicts class via majority vote.

        **Parameters**

        xtest : pd.DataFrame
            features for test set
        """
        r_xtest = com.convert_to_r_dataframe(xtest)
        pred = self.rf_pred(self.rf, r_xtest)
        py_pred = com.convert_robj(pred)
        genes, pred_class = zip(*py_pred.items())
        tmp_df = pd.DataFrame({'pred_class': pred_class},
                              index=genes)
        tmp_df = tmp_df.reindex(xtest.index)
        tmp_df -= 1  # for some reason the class numbers start at 1
        return tmp_df

    def predict_proba(self, xtest):
        """Predicts the probability for each class.

        **Parameters**

        xtest : pd.DataFrame
            features for test set
        """
        r_xtest = com.convert_to_r_dataframe(xtest)
        pred_prob = self.rf_pred_prob(self.rf, r_xtest)
        py_pred_prob = com.convert_robj(pred_prob)
        return py_pred_prob.values


class RRandomForest(GenericClassifier):

    def __init__(self, df,
                 total_iter=5,
                 weight=False,
                 min_ct=5):
        self.logger = logging.getLogger(__name__)
        onco_flag, tsg_flag = True, True  # classes to actually classify
        super(RRandomForest, self).__init__(total_iter,
                                            classify_oncogene=onco_flag,
                                            classify_tsg=tsg_flag)  # call base constructor
        # self.set_min_count(min_ct)
        self.is_weighted_sample = weight

        df = df.drop('total', axis=1)
        df = df.fillna(df.mean())
        self.x, self.y = features.randomize(df)

        # use the MyClassifier wrapper class around R
        self.clf = MyClassifier()
        self.clf.set_classes(onco_flag, tsg_flag)