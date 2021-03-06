import cv2 as cv
import numpy as np
from image_predictors import *
import huffman as huff
import ast, os

images = ["../raw/light.bmp", "../raw/marbles.bmp"]
INFINITE = 999999
EXECUTABLE = "./byte_stream"

def get_image_info(file_path):

    image = cv.imread(file_path, cv.IMREAD_GRAYSCALE)
    return image

def get_residuum(image, i, j, predictor):

    
    pvalue = predict_value(predictor, i, j, image)
    if not pvalue:
        return image[i,j]

    residuum = image[i, j] - pvalue

    return residuum

def predict_values(image, predictor):

    residuums = []

    (height, width) = image.shape
    for i in range(height):
        for j in range(width):
            residuum = get_residuum(image, i, j, predictor)
            residuums.append(residuum)

    return residuums

def get_huffman(image, predictor):

    residuums = predict_values(image, predictor)
    num_appearances = {}
    for residuum in residuums:
        if residuum not in num_appearances:
            num_appearances[residuum] = 1
        else:
            num_appearances[residuum] += 1

    huff_coll = []
    for entry in num_appearances:
        huff_coll += [(entry, num_appearances[entry])]

    huff_coll = huff.codebook(huff_coll)
    return (huff_coll, residuums)

def save_text_huffman(image, filename, predictor):

    stream = ""
    (codings, residuums) = get_huffman(image, predictor)

    for residuum in residuums:
        stream += codings[residuum]

    stream_file = open(filename, "w")
    dict_file = open(filename + ".dict", "w")

    stream_file.write(stream)
    dict_file.write(predictor + "\n")
    dict_file.write(str(image.shape) + "\n")
    dict_file.write(str(codings))

    stream_file.close()
    dict_file.close()

    os.system(EXECUTABLE + " u " + filename + " "  + filename + ".arch")
    os.system("rm -f " + filename)

def load_text_huffman(filename):

    if ".arch" not in filename:
        print "Not a valid format... We need .arch files"
        return None

    tmp_file = filename.split(".arch")[0]
    os.system(EXECUTABLE + " v " + filename + " " + tmp_file)
 
    stream_file = open(tmp_file, "r")
    dict_file = open(tmp_file + ".dict", "r")

    stream = stream_file.read()
    predictor = dict_file.readline().split('\n')[0]
    shape = ast.literal_eval(dict_file.readline())
    codings = ast.literal_eval(dict_file.read())
    stream_file.close()
    dict_file.close()

    return (codings, stream, shape, predictor)

def decode_residuums(filename):

    (codings, stream, shape, predictor) = load_text_huffman(filename)
    decodings = {}
    residuums = []
    for (key, value) in codings.iteritems():
        decodings[value] = key

    key = ""
    index = 0
    i = 0
    while index < len(stream):
        key += stream[index]
        index += 1
        if key in decodings:
            residuums += [decodings[key]]
            key = ""

    return (residuums, shape, predictor)

def restore_image(filename):

    (residuums, shape, predictor) = decode_residuums(filename)
    (height, width) = shape
    blank_image = np.zeros(shape, np.uint8)
    index = 0
    for i in range(height):
        for j in range(width):
            blank_image[i,j] = restore_value(predictor, i, j, residuums[index], blank_image)
            index += 1
    return blank_image
 
def compress_statistics(image):

    residuums = predict_values(image)
    (height, width) = image.shape
    num_bits = 0

    """ Decoment this following section if you want to visualize the residuum
    new_image = np.zeros((height, width), np.uint8)
    for i in range(height):
        for j in range(width):
            new_image[i, j] = residuums[i * height + j]
    
    cv.imshow("residuum", new_image)
    cv.waitKey(0)
    """
    for residuum in residuums:
        if residuum != 0:
            num_bits += int.bit_length(int(residuum))

    print ("Original image has the size of: " + str(image.size * 8) + " bits")
    print ("Compressed file has the size of: " + str(num_bits) + " bits")
    print ("Compression ratio is the size of " + str(float(num_bits) / (image.size * 8)))


if __name__ == "__main__":
    image = get_image_info(images[1])
    save_text_huffman(image, "marbles.temp", "N")
    blank_image = restore_image("marbles.temp.arch")
    cv.imshow("imagine", blank_image)
    cv.waitKey()
    cv.imwrite("image.bmp", blank_image)
