1. * Alter the scraping function to obtain All-star apperances as well
2. * Start creating a two-step bespoke model that cuts out ineligible players by hand (must be on track to have played 20 minutes in 65 games)
3. * 'Games started' seems to be important but we should probably make it a ratio of total games played to that point so that all features are per-game and then the model could be applied mid season 
4. * Test Logistic Regression as a means for classifying vote receivers
5. * Try considering whether or not a player was MVP within the last 2-3 years? maybe categorical with the category being 0, 1, 2 meaning didnt win, won last year, won the last two years? (Or just boolean)
6. * Work on quasibinomial regressor for predicting vote share
7. Remove non-total traded player stat entries 
8. Make a function for finding feature subsets for a generic model in utils.py
9. **(cond logit for MVP done) Clean up the classifier and regressor notebooks, try XGBoost for classifier and cond. logit for MVP
10. * hyperparameter tuning needs to be done in both the classifiers and the regressors