//------------------------------------------------
///// NAME: Victor Ezendu 
///// STUDENT NUMBER: 7856953
///// COURSE: COMP 3430, SECTION: A01
///// INSTRUCTOR: Robert Guderian
///// ASSIGNMENT: 2, QUESTION: 2
///// 
///// REMARKS: Multiple threads
/////----------------------------------------------

#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <ctype.h>
#include <assert.h>
#include <unistd.h>

void *work(void *arg);
char *get();
void put(char *value);
void producer();

int filesCount = 640;
#define BUFFER_SIZE 1
#define outputFileNo 27
int threadCount;
int count = 0;
int argvPos = 2;
int args;
int countOfFilesDone = 0;
pthread_mutex_t newMutex = PTHREAD_MUTEX_INITIALIZER;
char *buffer[BUFFER_SIZE];
pthread_cond_t empty, fill = PTHREAD_COND_INITIALIZER;
pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;
FILE *outputFile[outputFileNo];
pthread_mutex_t outputLocks[outputFileNo];


int main(int argc, char *argv[])
{
	args = argc-2; //minus program name and no of threads
			
	//create 27 output files as a.txt, b.txt....others.txt
	char outputFileName[10]; //size of the longest output file name (other.txt)
		
	for(int i = 0; i<outputFileNo; i++)
	{
		if(i == 26)
		{
			sprintf(outputFileName, "%s.txt", "other");
		}	
		else
		{
			sprintf(outputFileName, "%c.txt", 'a'+i);
		}
				
			outputFile[i] = fopen(outputFileName, "a");
						
	}


	//create 27 locks for the 27 files
	for(int i = 0; i<outputFileNo; i++)
	{
		pthread_mutex_init(&outputLocks[i], NULL);
	}

	//create argv[1] number of thread workers
	threadCount = atoi(argv[1]);
	pthread_t worker[threadCount];
	printf("creating %d threads to process %d files\n", threadCount, args);
	
	for (int i = 0; i< threadCount; i++)
	{
		pthread_create(&worker[i], NULL, work, 	NULL);
	}

	//producer
	for (int i = 2; i < argc; i++) { //start at position 2 in argv array to start taking filenames3

		pthread_mutex_lock(&mutex); 
		while (count == BUFFER_SIZE) 
			pthread_cond_wait(&empty, &mutex); 
		put(argv[i]); 
		pthread_cond_signal(&fill); 
		pthread_mutex_unlock(&mutex);
	}

	//we just passed in the last file to process so wait for the thread handling the file to finish
	sleep(3);
	
	//we are done with processing all files, send a signal to all threads to quit
	pthread_cond_broadcast(&fill);

	//close output files
	for(int i = 0; i<outputFileNo; i++)
	{
		fclose(outputFile[i]);
	}

	printf("Done!\n");
	return EXIT_SUCCESS;
}


char *get() 
{
	char *tmp = buffer[0];
	assert(count == 1);
	count = 0;
	return tmp;
}

void put(char *value) 
{

	assert(count == 0);
	count = 1;
	buffer[0] = value;	

}


void *work(void *arg)
{
	(void) arg;

	while (countOfFilesDone != args)
	{
		pthread_mutex_lock(&mutex); 
		while (count == 0)
		{ 
			pthread_cond_wait(&fill, &mutex);
			if(countOfFilesDone == args)
			{
				printf("we are done processing all files so all threads are getting exited\n");
				pthread_exit(NULL);
			}
		}
		char *tmp = get(); //get filename
		pthread_cond_signal(&empty);

		//start processing file
		FILE *fd = fopen(tmp, "r");
		int MAX_VALUE = 100;
		char word[MAX_VALUE]; //assume a word will not exceed 100 chars

		while(fscanf(fd, "%s", word) == 1)
		{
			if(isalpha(word[0])) //word[0] is an alphabet
			{
				int pos = tolower(word[0]) - 'a'; //this will convert the first word to lower case and get correct position to put word in outputfile array
				pthread_mutex_lock(&outputLocks[pos]);
				fprintf(outputFile[pos], "%s\n", word);
				pthread_mutex_unlock(&outputLocks[pos]);
			}

			else
			{
				pthread_mutex_lock(&outputLocks[outputFileNo-1]);
				fprintf(outputFile[outputFileNo-1],"%s\n", word);
				pthread_mutex_unlock(&outputLocks[outputFileNo-1]);
			}

		}	

		printf("File %s is done being processed\n", tmp);
		fclose(fd); //close inputfile
	
		//update no of files done processing
		pthread_mutex_lock(&newMutex);
		countOfFilesDone++;
		pthread_mutex_unlock(&newMutex);

		pthread_mutex_unlock(&mutex);
	}

	pthread_exit(NULL);	

}
