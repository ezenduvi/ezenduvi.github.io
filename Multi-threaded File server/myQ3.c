//------------------------------------------------
///// NAME: Victor Ezendu 
///// STUDENT NUMBER: 7856953
///// COURSE: COMP 3430, SECTION: A01
///// INSTRUCTOR: Robert Guderian
///// ASSIGNMENT: 2, QUESTION: 3
///// 
///// REMARKS: FIFOs with threads
/////----------------------------------------------

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <ctype.h>
#include <assert.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/stat.h>  
#include <string.h>
#include <fcntl.h>
#include <wait.h>
#include <errno.h>
#include <sys/resource.h>


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
const char *fifo[outputFileNo];
int fifoFd[outputFileNo];


int main(int argc, char *argv[])
{

	args = argc-2;
	
	//create 27 outputfiles and 27 fifos and open them 	 
	//create 27 output files as a.txt, b.txt....other.txt
	char outputFileName[10]; //size of the longest output file name (other.txt)
	char outputFifoName[6]; //size of longest fifo name (other)
	
		
	for(int i = 0; i<outputFileNo; i++)
	{
		if(i == 26)
		{
			sprintf(outputFileName, "%s.txt", "other");
			sprintf(outputFifoName, "%s", "other");
		}	
		else
		{
			sprintf(outputFileName, "%c.txt", 'a'+i);
			sprintf(outputFifoName, "%c", 'a'+i);
		}
				
			outputFile[i] = fopen(outputFileName, "a");
			fifo[i] = outputFifoName;
			int result = mkfifo(fifo[i], 0600);
			if (result) {
				perror("Unable to create named pipe");
				exit(EXIT_FAILURE);
			}
			fifoFd[i] = open(fifo[i], O_RDWR | O_NONBLOCK);
			printf("fifo named %s has been created\n", outputFifoName);
						
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
	
	//create 27 new processes that writes all data in fifos to their respective files
	pid_t child;

	for (int i = 0; i < outputFileNo; i++) 
	{
	        child = fork();

	        if (child == -1)
		{
        		perror("Error forking child process");
            		exit(EXIT_FAILURE);
        	} 
		else if (child == 0) 
		{
            		// Child process
			int MAX_VALUE = 100;
            		char word[MAX_VALUE];
            		int bytesRead;

  	       		while ((bytesRead = read(fifoFd[i], word, MAX_VALUE)) > 0) 
			{
        	        	
				for (int j = 0; j < bytesRead; j++) 
				{
        				if (word[j] == ' ')
					{
						fprintf(outputFile[i], "%c\n", word[j]);
            				} 
					else 
					{
						fprintf(outputFile[i], "%c", word[j]);	
            				}
        			}
				
				fprintf(outputFile[i], "%s\n", "");
            		}

            		close(fifoFd[i]);
            		fclose(outputFile[i]);
           		exit(EXIT_SUCCESS);
        	}
	}

    	// wait for child processes to finish
    	for (int i = 0; i < outputFileNo; i++) 
	{
        	wait(NULL);
	}

    	// Close all the FIFOs and files in parent
	for (int i = 0; i < outputFileNo; i++) 
	{
        	close(fifoFd[i]);
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
				//fprintf(outputFile[pos], "%s\n", word);
				//write to fifo
				
				 printf("Pipe size: %d\n", fcntl(fifoFd[pos], F_GETPIPE_SZ));

				int x = write(fifoFd[pos], word, strlen(word));
				if(x == -1)
				{
					perror("write");
				}
			
				printf("%d bytes were written to fifo %d\n", x, pos);
				write(fifoFd[pos], " ", 1);
			}

			else
			{
				printf("Pipe size: %d\n", fcntl(fifoFd[outputFileNo-1], F_GETPIPE_SZ));
				
				//write to other fifo
				int x = write(fifoFd[outputFileNo-1], word, strlen(word));
				if(x == -1)
				{
					perror("write");
				}

				printf("%d bytes were written to fifo %d\n", x, outputFileNo-1);
				
			}

		}	

		printf("File %s has been written to fifo\n", tmp);
		fclose(fd); //close inputfile
	
		//update no of files done processing
		pthread_mutex_lock(&newMutex);
		countOfFilesDone++;
		pthread_mutex_unlock(&newMutex);

		pthread_mutex_unlock(&mutex);
	}

	pthread_exit(NULL);	

}
