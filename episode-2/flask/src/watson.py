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

import os
import json

from flask import Flask, jsonify, render_template, redirect, session, url_for
from flask.ext.wtf import Form
from wtforms import TextAreaField, SubmitField
from wtforms.validators import Required

from watson_developer_cloud import LanguageTranslatorV2 as LanguageTranslation
from watson_developer_cloud import WatsonException


# Initialise the application and the secret key needed for CSRF
# protected form submission.
# You should change the secret key to something that is secret and complex.


app = Flask(__name__)
app.config['SECRET_KEY'] = \
    'please subtitute this string with something hard to guess'


global username
global password
with open('credentials.json') as f:
    data = json.load(f)
    credentials = data['language_translator'][0]['credentials']
    username = str(credentials['username'])
    password = str(credentials['password'])


# The form containing the text to be processed that the
# application web page will be submitted/


class LangForm(Form):
    txtdata = TextAreaField('Text to process', validators=[Required()])
    submit = SubmitField('Process')


def getTranslationService():
    '''
    Args:
        None
    Returns:
        LanguageTranslation (class): this is just a wrapper for the
        service credentials
    '''
    return LanguageTranslation(username=username, password=password)


def identifyLanguage(data):
    '''
    Args:
        data (str): this is the string representing the words in the language
        being identified and translated
    Returns:
        retData (dict): this is the dict which has the data for the first
        language identified by watson
    '''
    txt = data.encode('utf-8', 'replace')
    language_translation = getTranslationService()

    langsdetected = language_translation.identify(txt)
    app.logger.info(json.dumps(langsdetected, indent=2))
    app.logger.info(langsdetected['languages'][0]['language'])
    app.logger.info(langsdetected['languages'][0]['confidence'])

    primarylang = langsdetected['languages'][0]['language']
    confidence = langsdetected['languages'][0]['confidence']

    retData = {'language': primarylang,
               'confidence': confidence}

    return retData


def checkForTranslation(fromlang, tolang):
    '''
    Args:
        fromlang (str): this is the language that has been detected by the
        translation service
        tolang (str): this is the language for which the ability to translate
        is being checked
    Returns:
        supportedModels (list): this list contains the languages that the
        detected language can be translated into
    '''
    msg = "Checking if possible to translate from {} to en".format(fromlang)
    app.logger.info(msg)
    supportedModels = []

    lt = getTranslationService()
    models = lt.get_models()
    app.logger.info(json.dumps(models, indent=2))
    if models and models['models']:
        modelList = models['models']
        for model in modelList:
            if fromlang == model['source'] and tolang == model['target']:
                supportedModels.append(model['model_id'])

    app.logger.info(supportedModels)
    return supportedModels


def performTranslation(txt, primarylang, targetlang):
    '''
    Args:
        txt (str): this is the string that is going to be translated
        primarylang (str): this is the language that was detected
        from the string
        targetlang (str): this is the language that txt is going to be
        translated into
    Returns:
        translation (str): this is the translated version of txt
    '''
    lt = getTranslationService()
    translation = lt.translate(txt, source=primarylang, target=targetlang)
    return translation


# As this is the only route defined in this application, so far,
# it is the only page that the application will respond to.
@app.route('/wl/lang', methods=['GET', 'POST'])
def wlhome():
    # This is how you do logging, in this case information messages.
    app.logger.info('wlhome page requested')
    allinfo = {}
    outputTxt = "TBD"
    targetlang = 'en'
    form = LangForm()
    # If the form passes this check, then its a POST and
    # the fields are valid. ie. if the
    # request is a GET then this check fails.
    if form.validate_on_submit():
        data = form.txtdata.data
        app.logger.info('Text to bne processed is {}'.format(data))
        lang = "TBC"
        try:
            lang = identifyLanguage(data)
            primarylang = lang['language']
            confidence = lang['confidence']
            outputTxt = "I am {} confident that the language is {}"
            outputTxt = outputTxt.format(confidence, primarylang)
            if targetlang != primarylang:
                app.logger.info("Language {} is not {}".format(primarylang,
                                                               targetlang))
                supportedModels = checkForTranslation(primarylang, targetlang)
                if supportedModels:
                    message = "We have some supported translation models"
                    app.logger.info(message)
                    englishTxt = \
                        performTranslation(data, primarylang, targetlang)
                    outputTxt += ", which in english is {}".format(englishTxt)
                else:
                    outputTxt += ", which unfortunately, we can't translate"
            allinfo['lang'] = outputTxt
            allinfo['form'] = form
            return render_template('watson/wlindex.html', info=allinfo)
        except WatsonException as err:
            allinfo['error'] = err
    allinfo['lang'] = session.get('langtext')
    allinfo['form'] = form
    return render_template('watson/wlindex.html', info=allinfo)


port = os.getenv('PORT', '5000')


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(port), debug=True)
