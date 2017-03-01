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

# from watson_developer_cloud import LanguageTranslatorV2 as LanguageTranslation
from watson_developer_cloud import WatsonException

from languagetranslation import LanguageTranslationUtils
from naturallanguageclassification import NaturalLanguageClassifierUtils


app = Flask(__name__)
app.config['SECRET_KEY'] = \
    'please subtitute this string with something hard to guess'


class LangForm(Form):
    txtdata = TextAreaField('Text to process', validators=[Required()])
    submit = SubmitField('Process')


@app.route('/wl/lang', methods=['GET', 'POST'])
def wlhome():
    app.logger.info('wlhome page requested')
    allinfo = {}
    outputTxt = "TBD"
    targetlang = 'en'
    lang = "TBD"
    txt = None
    form = LangForm()
    if form.validate_on_submit():
        lang = "TBC"
        txt = form.txtdata.data
        form.txtdata.data = ''

        try:
            ltu = LanguageTranslationUtils(app)
            nlcu = NaturalLanguageClassifierUtils(app)
            lang = ltu.identifyLanguage(txt)
            primarylang = lang["language"]
            confidence = lang["confidence"]

            outputTxt = "I am {} confident that the language is {}"
            outputTxt = outputTxt.format(confidence, primarylang)
            if targetlang != primarylang:
                supportedModels = ltu.checkForTranslation(primarylang,
                                                          targetlang)
                if supportedModels:
                    englishTxt = ltu.performTranslation(txt, primarylang,
                                                        targetlang)
                    outputTxt += ", which in english is %s" % englishTxt
                    classification = nlcu.classifyTheText(englishTxt)
                else:
                    outputTxt += \
                        ", which unfortunately we can't translate into English"
            else:
                classification = nlcu.classifyTheText(txt)
            if classification:
                message = "(and {} confident that it is {} classification)"
                message = message.format(classification['confidence'],
                                         classification['className'])
                outputTxt += message

            session['langtext'] = outputTxt

            allinfo['lang'] = lang
            allinfo['form'] = form
            return redirect(url_for('wlhome'))
        except WatsonException as err:
            allinfo['error'] = err

    allinfo['lang'] = session.get('langtext')
    allinfo['form'] = form
    return render_template('watson/wlindex.html', info=allinfo)


port = os.getenv('PORT', '5000')


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(port), debug=True)
