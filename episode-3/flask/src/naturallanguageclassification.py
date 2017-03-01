# -*- coding: utf-8 -*-
# Copyright 2016 IBM Corp. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json

from watson_developer_cloud import WatsonException
from watson_developer_cloud import NaturalLanguageClassifierV1 as NaturalLanguageClassifier


with open('class_credentials.json') as f:
    data = json.load(f)
    username = str(data['username'])
    password = str(data['password'])


class NaturalLanguageClassifierUtils(object):
    def __init__(self, app):
        super(NaturalLanguageClassifierUtils, self).__init__()
        self.app = app
        self.service = NaturalLanguageClassifier(username=username,
                                                 password=username)

    def getNLCService(self):
        '''
        Args:
            None
        Returns:
            NaturalLanguageClassifierUtils as a class
        '''
        return self.service

    def classifyTheText(self, txt):
        '''
        Args:
            txt (str): this is the string that is going to be classified
        Returns:
            classification (dict): this is a dict representing the classifier
            output
        '''
        self.app.logger.info("About to run the classification")
        nlc = self.getNLCService()
        classification = {}

        classificationList = nlc.list()
        if "classifiers" in classificationList:
            if "classifier_id" in classificationList["classifiers"][0]:
                classID = classificationList["classifiers"][0]['classifier_id']
                status = nlc.status(classID)
                if status.get("status") == "Available":
                    classes = nlc.classify(classID, txt)
                    if "classes" in classes:
                        className = classes["classes"][0]["class_name"]
                        confidence = classes["classes"][0]["confidence"]
                        classification = {"confidence": confidence,
                                          "className": className}
                        self.app.logger.info(classification)
        return classification
