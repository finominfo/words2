input_string = "+goodTranslate1 -badTranslate1 +goodTranslate2 +goodTranslate3 +goodTranslate4 -badTranslate2"

translations = input_string.split()

goodTranslates = [translate[1:] for translate in translations if translate.startswith('+')]
badTranslates = [translate[1:] for translate in translations if translate.startswith('-')]

print("goodTranslates:", goodTranslates)
print("badTranslates:", badTranslates)


# Do VICA VERSA

result = ' '.join(['+' + translate for translate in goodTranslates] +
                  ['-' + translate for translate in badTranslates])

print(result)