import sh
import os

fp = "./input"
for fname in os.listdir(fp):
    fname = os.path.join(fp, fname)
    if fname.endswith('.pdf'):
        #sh.command('convert', fname, fname.replace('pdf', 'png'))
        sh.command('convert', '-density', '350', fname, fname.replace('pdf', 'png'))

sh.command('generate-md', '--layout mixu-page --input ./input  --output ./output')

# mixu-book
# toc
