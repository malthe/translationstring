import unittest

class TestTranslationString(unittest.TestCase):
    def _makeOne(self, msgid, **kw):
        from internatl import TranslationString
        return TranslationString(msgid, **kw)

    def test_is_unicode_subclass(self):
        inst = self._makeOne('msgid')
        self.failUnless(isinstance(inst, unicode))

    def test_msgid_is_translation_string(self):
        another = self._makeOne('msgid', domain='domain', default='default',
                                mapping={'a':1})
        result = self._makeOne(another)
        self.assertEqual(result, 'msgid')
        self.assertEqual(result.domain, 'domain')
        self.assertEqual(result.default, 'default')
        self.assertEqual(result.mapping, {'a':1})

    def test_default_None(self):
        inst = self._makeOne('msgid')
        self.assertEqual(inst, 'msgid')
        self.assertEqual(inst.default, 'msgid')

    def test_default_not_None(self):
        inst = self._makeOne('msgid', default='default')
        self.assertEqual(inst, 'msgid')
        self.assertEqual(inst.default, 'default')

    def test_allargs(self):
        inst = self._makeOne('msgid', domain='domain', default='default',
                             mapping='mapping')
        self.assertEqual(inst, 'msgid')
        self.assertEqual(inst.default, 'default')
        self.assertEqual(inst.mapping, 'mapping')
        self.assertEqual(inst.domain, 'domain')

    def test_interpolate_substitution(self):
        mapping = {"name": "Zope", "version": 3}
        inst = self._makeOne('This is $name version ${version}.',
                              mapping=mapping)
        result = inst.interpolate()
        self.assertEqual(result, u'This is Zope version 3.')

    def test_interpolate_subsitution_more_than_once(self):
        mapping = {"name": "Zope", "version": 3}
        inst = self._makeOne(
            u"This is $name version ${version}. ${name} $version!",
            mapping=mapping)
        result = inst.interpolate()
        self.assertEqual(result, u'This is Zope version 3. Zope 3!')

    def test_interpolate_double_dollar_escape(self):
        mapping = {"name": "Zope", "version": 3}
        inst = self._makeOne('$$name', mapping=mapping)
        result = inst.interpolate()
        self.assertEqual(result, u'$$name')

    def test_interpolate_missing_not_interpolated(self):
        mapping = {"name": "Zope", "version": 3}
        inst = self._makeOne(
            u"This is $name $version. $unknown $$name $${version}.",
            mapping=mapping)
        result = inst.interpolate()
        self.assertEqual(result,
                         u'This is Zope 3. $unknown $$name $${version}.')

    def test_interpolate_missing_mapping(self):
        inst = self._makeOne(u"This is ${name}")
        result = inst.interpolate()
        self.assertEqual(result, u'This is ${name}')

    def test_interpolate_passed_translated(self):
        mapping = {"name": "Zope", "version": 3}
        inst = self._makeOne(u"This is ${name}", mapping = mapping)
        result = inst.interpolate('That is ${name}')
        self.assertEqual(result, u'That is Zope')

class TestTranslationStringFactory(unittest.TestCase):
    def _makeOne(self, domain):
        from internatl import TranslationStringFactory
        return TranslationStringFactory(domain)

    def test_allargs(self):
        factory = self._makeOne('budge')
        inst = factory('msgid', mapping='mapping', default='default')
        self.assertEqual(inst, 'msgid')
        self.assertEqual(inst.domain, 'budge')
        self.assertEqual(inst.mapping, 'mapping')
        self.assertEqual(inst.default, 'default')


class TestChameleonTranslate(unittest.TestCase):
    def _makeOne(self, translator):
        from internatl import ChameleonTranslate
        return ChameleonTranslate(translator)

    def test_msgid_nonstring(self):
        translate = self._makeOne(None)
        result = translate(None)
        self.assertEqual(result, None)

    def test_msgid_translationstring_translator_is_None(self):
        msgid = DummyTranslationString('abc')
        translate = self._makeOne(None)
        result = translate(msgid)
        self.assertEqual(result, 'interpolated')

    def test_msgid_unicode_translator_is_None(self):
        msgid = u'foo'
        translate = self._makeOne(None)
        result = translate(msgid)
        self.assertEqual(result, u'foo')

    def test_msgid_translationstring_translator_is_not_None(self):
        msgid = DummyTranslationString()
        def translator(msg):
            return msg
        translate = self._makeOne(translator)
        result = translate(msgid)
        self.assertEqual(result, msgid)

    def test_msgid_unicode_translator_is_not_None(self):
        msgid = 'foo'
        def translator(msg):
            return msg
        translate = self._makeOne(translator)
        result = translate(msgid)
        self.assertEqual(result, msgid)

class TestTranslator(unittest.TestCase):
    def _makeOne(self, translations=None, policy=None):
        from internatl import Translator
        return Translator(translations, policy)

    def test_translations_None_interpolation_required(self):
        inst = self._makeOne()
        tstring = DummyTranslationString('$abc', mapping=True)
        result = inst(tstring)
        self.assertEqual(result, 'interpolated')
        
    def test_translations_None_interpolation_not_required(self):
        inst = self._makeOne()
        tstring = DummyTranslationString('msgid', mapping=False)
        result = inst(tstring)
        self.assertEqual(result, 'msgid')

    def test_policy_returns_msgid(self):
        tstring = DummyTranslationString('msgid', default='default')
        def policy(translations, msg):
            return msg
        inst = self._makeOne('ignoreme', policy)
        result = inst(tstring)
        self.assertEqual(result, 'default')

    def test_policy_returns_translation(self):
        tstring = DummyTranslationString('msgid')
        def policy(translations, msg):
            return 'translated'
        inst = self._makeOne('ignoreme', policy)
        result = inst(tstring)
        self.assertEqual(result, 'translated')

class TestPluralizer(unittest.TestCase):
    def _makeOne(self, translations=None, policy=None):
        from internatl import Pluralizer
        return Pluralizer(translations, policy)

    def test_translations_None_interpolation_required(self):
        inst = self._makeOne()
        result = inst('$abc', '$abc', 1, mapping={'abc':1})
        self.assertEqual(result, '1')
        
    def test_translations_None_interpolation_not_required(self):
        inst = self._makeOne()
        result = inst('msgid', 'msgid', 1)
        self.assertEqual(result, 'msgid')

    def test_policy_returns_translated(self):
        translations = DummyTranslations('result')
        def policy(translations, singular, plural, n, domain):
            return 'translated'
        inst = self._makeOne(translations, policy)
        tstring = DummyTranslationString('msgid')
        result = inst(tstring, tstring, 1)
        self.assertEqual(result, 'translated')

class Test_ugettext_policy(unittest.TestCase):
    def _callFUT(self, translations, tstring):
        from internatl import ugettext_policy
        return ugettext_policy(translations, tstring)

    def test_it(self):
        translations = DummyTranslations('result')
        result = self._callFUT(translations, 'string')
        self.assertEqual(result, 'result')

class Test_dugettext_policy(unittest.TestCase):
    def _callFUT(self, translations, tstring):
        from internatl import dugettext_policy
        return dugettext_policy(translations, tstring)

    def test_it_use_default_domain(self):
        translations = DummyTranslations('result', domain=None)
        tstring = DummyTranslationString()
        result = self._callFUT(translations, tstring)
        self.assertEqual(result, 'result')
        self.assertEqual(translations.asked_domain, 'messages')

    def test_it_use_translations_domain(self):
        translations = DummyTranslations('result', domain='notdefault')
        tstring = DummyTranslationString()
        result = self._callFUT(translations, tstring)
        self.assertEqual(result, 'result')
        self.assertEqual(translations.asked_domain, 'notdefault')

    def test_it_use_tstring_domain(self):
        translations = DummyTranslations('result', domain='notdefault')
        tstring = DummyTranslationString(domain='exact')
        result = self._callFUT(translations, tstring)
        self.assertEqual(result, 'result')
        self.assertEqual(translations.asked_domain, 'exact')

    def test_it_translations_has_no_dugettext(self):
        translations = DummyTranslations('result', domain='foo')
        tstring = DummyTranslationString('abc')
        translations.dugettext = None
        result = self._callFUT(translations, tstring)
        self.assertEqual(result, 'result')

class Test_ungettext_policy(unittest.TestCase):
    def _callFUT(self, translations, singular, plural, n, domain=None,
                 mapping=None):
        from internatl import ungettext_policy
        return ungettext_policy(translations, singular, plural, n, domain)

    def test_it(self):
        translations = DummyTranslations('result')
        result = self._callFUT(translations, 'singular', 'plural', 1)
        self.assertEqual(result, 'result')

class Test_dungettext_policy(unittest.TestCase):
    def _callFUT(self, translations, singular, plural, n, domain=None,
                 mapping=None):
        from internatl import dungettext_policy
        return dungettext_policy(translations, singular, plural, n, domain)

    def test_it_use_default_domain(self):
        translations = DummyTranslations('result')
        result = self._callFUT(translations, 'singular', 'plural', 1)
        self.assertEqual(result, 'result')
        self.assertEqual(translations.asked_domain, 'messages')

    def test_it_use_translation_domain(self):
        translations = DummyTranslations('result', domain='translation')
        result = self._callFUT(translations, 'singular', 'plural', 1, None)
        self.assertEqual(result, 'result')
        self.assertEqual(translations.asked_domain, 'translation')

    def test_it_use_passed_domain(self):
        translations = DummyTranslations('result', domain='translation')
        result = self._callFUT(translations, 'singular', 'plural', 1, 'domain')
        self.assertEqual(result, 'result')
        self.assertEqual(translations.asked_domain, 'domain')

    def test_it_translations_has_no_dungettext(self):
        translations = DummyTranslations('result', domain='translation')
        translations.dungettext = None
        result = self._callFUT(translations, 'singular', 'plural', 1, 'domain')
        self.assertEqual(result, 'result')

class DummyTranslations(object):
    def __init__(self, result, domain=None):
        self.result = result
        self.domain = domain

    def ugettext(self, tstring):
        return self.result

    def dugettext(self, domain, tstring):
        self.asked_domain = domain
        return self.result

    def ungettext(self, singular, plural, n):
        return self.result

    def dungettext(self, domain, singular, plural, n):
        self.asked_domain = domain
        return self.result

class DummyTranslationString(unicode):
    def __new__(cls, msgid='', domain=None, default=None, mapping=None):
        self = unicode.__new__(cls, msgid)
        unicode.__init__(self, msgid)
        self.domain = domain
        self.mapping = mapping
        if default is None:
            default = msgid
        self.default = default
        return self
        
    def interpolate(self, translated=None):
        return 'interpolated'
    
