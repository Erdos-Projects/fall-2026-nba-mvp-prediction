import sys
from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.base import BaseEstimator, RegressorMixin, clone
from sklearn.utils.validation import check_is_fitted

ROOT=Path.cwd()
while not (ROOT / ".git").exists() and ROOT!=ROOT.parent:
    ROOT=ROOT.parent
sys.path.insert(0, str(ROOT / "src"))

import utils

class ClassifiedRegressor(BaseEstimator, RegressorMixin):
    '''
    
    '''
    
    def __init__(self, classifier, regressor, threshold=.5, check_eligibility=True):
        self.regressor = regressor
        self.check_eligibility = check_eligibility
        self.classifier = classifier
        self.threshold = threshold
            
    
    def _eligible(self, X):
        """Removes players with less than 73% of games played or less than 15 minutes per game"""
        try:
            if self.check_eligibility:
                return np.asarray((X['GP%'] >= .73) & (X['MP'] >= 15.0), dtype=bool)
            else:
                return np.asarray([1]*len(X),dtype=bool)
        except:
            raise ValueError("Something went wrong.  Does the training data have 'GP%' and 'MP' columns?")
    
    def _label(self, y):
        """Labels 1 or 0 depending on if player received MVP votes.  This is the target data for the classifier."""
        try:
            return pd.Series(np.asarray(y > 0.0, dtype=int))
        except:
            raise ValueError("Something went wrong.  Does the target data have an 'MVPVS' column?")
    
    def _internal_chaining(self, X):
        '''
        Creates an index set for internal chaining so that the regressor is being trained on data that the classifier labels without having been trained on first.
        For example, if 10 years of training data are sent in, classifiers are trained on splits with year 1, years 1-2, years 1-3... up to years 1-9.  Each of these
        trained classifiers are used to predict on year 2, 3,...,10 respectively.  The totality of the predicted data is then sent to train the regressor.  The classifier
        is simply trained on all 10 years.
        '''
        try:
            years = X.Year
            return list(utils.forward_chaining_splits(years))
        except:
            raise ValueError("Does your training data have a 'Year' column?")
    
    def fit(self, X, y):
        '''
        Typical fit function but the X column must contain the following columns:
        
        'Year'
        'GP%'
        'MP'
        
        These will not be used as training data.
        '''
        if not {'Year','GP%','MP'}.issubset(X.columns):
            raise ValueError('training data must contain the "Year", "GP%" and "MP" columns')
        # remove ineligible players and prepare target data
        X = X.sort_values('Year')
        y = y.loc[X.index]
        X_e, y_e = X[self._eligible(X)], y[self._eligible(X)]
        y_l = self._label(y_e)
        
        # create the classified data for training the regressor
        # self.cv_ = self._internal_chaining(X_e)
        X_e = X_e.drop(columns=['Year','GP%','MP'])
        # reg_mask = np.zeros(len(self.cv_[0][0]))
        # for chain in self.cv_:
        #     tmp_classifier_ = clone(self.classifier).fit(X_e.iloc[chain[0]], y_l.iloc[chain[0]])
        #     reg_mask = np.append(reg_mask, tmp_classifier_.predict_proba(X_e.iloc[chain[1]])[:,1])
        # reg_mask = (reg_mask > self.threshold)
        reg_mask = np.array([True]*len(X_e))

        
        # train the classifier on all eligible data
        self.classifier_ = clone(self.classifier).fit(X_e, y_l)
        
        # train the regressor on the forward chained output of the classifier
        self.regressor_ = clone(self.regressor).fit(X_e[reg_mask], y_e[reg_mask])
        
        return self
    
    def predict(self, X):
        '''
        Typical predict function but the X column must contain the following columns:
        
        'GP%'
        'MP'
        
        These will not be used to predict.
        '''
        if not {'GP%','MP'}.issubset(X.columns):
            raise ValueError('data must contain the "GP%" and "MP" columns')
        check_is_fitted(self)
        
        X_e = X[self._eligible(X)]
        X_e = X_e.drop(columns=['GP%','MP'])
        if 'Year' in X.columns:
            X_e = X_e.drop(columns='Year')
        mask = (self.classifier_.predict_proba(X_e)[:,1] > self.threshold)
        X_r = X_e[mask]
        idx = X_r.index
        
        out = pd.Series(0.0, index=X.index)
        if mask.any():
            out[idx] = self.regressor_.predict(X_r)
            
        return out
        
        

