#include <opencv2/opencv.hpp>
#include <iostream>
#include <sstream>
#include <vector>
#include <map>
#include <fstream>
#include <chrono>
using namespace std;
using namespace cv;

int main(int argc, char **argv) {
    cerr << "Reading image " << argv[1] << "..." << endl;
    Mat src_tmp = imread(argv[1], 0);

    for(int stitch = 1; stitch >= 1; stitch--) {

        for(int benchiter = 0; benchiter <= 0; benchiter++) {

            Mat src(6243, stitch * 6240, CV_8UC1);
            for(int x = 0; x < stitch; x++) {
                Rect roi(x*6240,0,6240,6243);
                src_tmp.copyTo(src(roi));
            }

            auto begin = chrono::high_resolution_clock::now();

            cerr << "Computing erode on CPU..." << endl;
            Mat d_erode;
            erode(src, d_erode, getStructuringElement(MORPH_RECT, Size(5,5)));
            src.release();
            cerr << "Computing dilate on CPU..." << endl;
            Mat d_dilate;
            dilate(d_erode, d_dilate, getStructuringElement(MORPH_RECT, Size(10,10)));
            d_erode.release();

            cerr << "Invert image on CPU..." << endl;
            Mat d_invert;
            Mat white(d_dilate.rows, d_dilate.cols, CV_8UC1, 255);
            subtract(white, d_dilate, d_invert);
            d_dilate.release();
            white.release();

            cerr << "Threshold image on CPU..." << endl;
            Mat d_thresh;
            threshold(d_invert, d_thresh, 128, 255, CV_THRESH_BINARY);
            d_invert.release();

            Mat circles;
            HoughCircles(d_thresh, circles, HOUGH_GRADIENT, 1, 100, 4, 10, 50, 200);
            cerr << "Circle count: " << circles.size() << endl;

            auto end = std::chrono::high_resolution_clock::now();
            if(benchiter > 0)
                cout << "CPU Hough," << stitch << "," << benchiter << "," << chrono::duration_cast<std::chrono::nanoseconds>(end-begin).count() << endl;
        }
    }

    return 0;
}

