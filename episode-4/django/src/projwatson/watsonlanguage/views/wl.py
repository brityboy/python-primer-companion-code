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

from django.shortcuts import render
from django import forms
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from watson_developer_cloud import WatsonException

from watsonlanguage.watsonutils.languagetranslation import LanguageTranslationUtils
from watsonlanguage.watsonutils.naturallanguageclassification import NaturalLanguageClassifierUtils

import json

import logging
logger = logging.getLogger(__name__)

class Form_language(forms.Form):
  txtdata = forms.CharField(required=True,
                             label="Text to Process",
                             widget=forms.Textarea)

def index(request):
  allinfo = {}
  outputTxt = "TBD"
  targetlang = 'en'
  classification = None
  form = None
  if request.POST:
    form = Form_language(request.POST)
    if form.is_valid():
      data = form.cleaned_data['txtdata']
      logger.info("Text to be process is %s" % data)
      lang = "TBD"

      try:
        ltu = LanguageTranslationUtils()
        nlcu = NaturalLanguageClassifierUtils()
        lang = ltu.identifyLanguage(data)
        primarylang = lang["language"]
        confidence = lang["confidence"]

        outputTxt = "I am %s confident that the language is %s" % (confidence, primarylang)
        if targetlang != primarylang:
          supportedModels = ltu.checkForTranslation(primarylang, targetlang)
          if supportedModels:
            englishTxt = ltu.performTranslation(data, primarylang, targetlang)
            outputTxt += ", which in english is %s" % englishTxt

            classification = nlcu.classifyTheText(englishTxt)
          else:
            outputTxt += ", which unfortunately we can't translate into English"
        else:
          classification = nlcu.classifyTheText(data)
        if classification:
          outputTxt += "(and %s confident that it is %s classification)" \
                                              % (classification['confidence'],
                                                 classification['className'])
      except WatsonException as err:
      	allinfo['error'] = err

      allinfo['lang'] = outputTxt
    else:
      allinfo['error'] = "The form is invalid" 
  else:
    form = Form_language
    
  allinfo['form'] = form
  return render(request, 'watson/wlindex.html', allinfo)


@csrf_exempt
def process(request):
  targetlang = 'en'
  classification = {"className":"unknown"}
  results = {}
  theData = {"error":"If you see this message then something has gone badly wrong"}

  validRequest = False
  logger.info("Checking request method")
  if request.method == "GET":
    logger.info("Request is a GET")
    data = "Hard coded string to test that API is returning something"
    validRequest = True

  if request.method == "POST":
    logger.info("Request is a POST")
    form = Form_language(request.POST)
    if form.is_valid():
      data = form.cleaned_data['txtdata']
      validRequest = True
    else:
      logger.info("The form is not valid")
  
  if validRequest:
    del theData["error"]
    try:
      ltu = LanguageTranslationUtils() 
      nlcu = NaturalLanguageClassifierUtils()     
      primarylang = theData['language'] = ltu.identifyLanguage(data)["language"]
      if targetlang != primarylang:
        supportedModels = ltu.checkForTranslation(primarylang, targetlang)
        if supportedModels:
          englishTxt = ltu.performTranslation(data, primarylang, targetlang)
          classification = nlcu.classifyTheText(englishTxt)
      else:
        classification = nlcu.classifyTheText(data)

      theData['classification'] = classification['className']
    except WatsonException as err:
      theData['error'] = err;
  else:
    theData['error'] = "The form data is invalid";
  
  results["results"] = theData
  return HttpResponse(json.dumps(results), content_type="application/json")

