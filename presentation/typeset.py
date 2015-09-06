import sh
import os

fp = "./input"
for fname in os.listdir(fp):
    fname = os.path.join(fp, fname)
    if fname.endswith('.pdf'):
        sh.command('convert', fname, fname.replace('pdf', 'png'))
        #sh.command('convert', '-density', '300', fname, fname.replace('pdf', 'png'))

sh.command('generate-md', '--layout mixu-book --input ./input  --output ./output')

#