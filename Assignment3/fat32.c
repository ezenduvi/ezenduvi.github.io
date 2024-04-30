//------------------------------------------------
///// NAME: Victor Ezendu 
///// STUDENT NUMBER: 7856953
///// COURSE: COMP 3430, SECTION: A01
///// INSTRUCTOR: Robert Guderian
///// ASSIGNMENT: 3, QUESTION: 1
///// 
///// REMARKS:reading fat32 volume
/////----------------------------------------------

#define _FILE_OFFSET_BITS 64
#include <stdio.h>
#include<stdlib.h>
#include"fat32.h"
#include<fcntl.h>
#include<stdint.h>
#include<unistd.h>
#include <string.h>
#include <stdbool.h>
#define MAX_TOKEN_SIZE 100
#define MAX_LONG_FILE_NAME 255

void bs_struct_reader(fat32BS *bsPointer, struct Fsinfo *fsInfoPointer, int handle);
uint32_t sectorToBytes(uint32_t secNo);
uint32_t clusterToBytes(uint32_t clusterNo);
void printDirectories(int handle, uint32_t clusterNo);
void extract_file_name(uint8_t *dir, char *file_name);
void extract_dir_name(uint8_t *dir, char *file_name);
uint32_t clusterToSector(uint32_t clusterNo);
void tokenizePath(const char* path, char** tokenArray, int* size);
void findAndReadFile(int handle, uint32_t clusterNo, char **tokenArray);
int readFileAndWrite(int handle, char *filename, uint32_t firstCluster, uint32_t fileSize);
 
uint32_t freeCount = 0;
fat32BS bsPointer;
struct Fsinfo fsInfoPointer; 
struct DirInfo dirInfo;
uint32_t dataSec;
uint32_t clusterCount;
uint32_t firstDataSector;
uint32_t clusterNo;
char *filename;
char *path;
int tokArrSize;
int arrIndex = 0;
bool foundFile = false;

int main(int argc, char *argv[])
{
	(void)argc;
	filename = argv[1];
	printf("File: %s\n", argv[1]);	

	int handle = open(filename, O_RDONLY);
	bs_struct_reader(&bsPointer, &fsInfoPointer, handle); //read in boot sector and fsInfo sector and verify them
	firstDataSector = bsPointer.BPB_RsvdSecCnt + (bsPointer.BPB_NumFATs * bsPointer.BPB_FATSz32);
	clusterNo = bsPointer.BPB_RootClus; //start at root directory

	if (strcmp(argv[2], "list") == 0) // Check if the second argument is "list"
	{ //output all files and directories on the drive
		lseek(handle, 0, SEEK_SET);
		printDirectories(handle, clusterNo);
	}
 
	else if (strcmp(argv[2], "info") == 0) // Check if the second argument is "info"
	{
		printf("Drive name: %s\n", bsPointer.BS_OEMName); //print drive name
		
		printf("Free space: %u kilobytes\n", clusterToBytes(freeCount)/1024); //print freecount clusters in kilobytes
 
		printf("Usable storage: %u kilobytes\n", clusterToBytes(clusterCount)/1024); //print usuable storage
	
		printf("Cluster count: %u in sectors or %u in kilobytes\n", clusterToSector(clusterCount), clusterToBytes(clusterCount));	
    	}
 
	else if (strcmp(argv[2], "get") == 0)// If the second argument is "get"
	{
		path = argv[3];
		char* tokenArray[MAX_TOKEN_SIZE];
				
		tokenizePath(path, tokenArray, &tokArrSize); //split path into tokens with / as delimeter

		lseek(handle, 0, SEEK_SET);
		findAndReadFile(handle, bsPointer.BPB_RootClus, tokenArray); //check if file is in path and then write it to a file
		if(!foundFile)
			printf("File could not be found\n");
				
	}
	
	close(handle); //close file handler
	
	return EXIT_SUCCESS;
}

//same function from lab4 to read in boot sector, fs info sector and verify it
void bs_struct_reader(fat32BS *bsPointer, struct Fsinfo *fsInfoPointer, int handle)
{
	read(handle, &bsPointer->BS_jmpBoot, 3);

	//validate jmpBoot[0]	
	if(((unsigned char) bsPointer->BS_jmpBoot[0] != 0xEB) && ((unsigned char) bsPointer->BS_jmpBoot[0] != 0xE9))
	{
		printf("Inconsistent file system: BS_jmpBoot must be 0xEB or 0xE9 and value is %02X\n", (unsigned char) bsPointer->BS_jmpBoot[0]);
		exit(0);
	}

	//keep reading other fields
	read(handle, &bsPointer->BS_OEMName, 8);
	read(handle, &bsPointer->BPB_BytesPerSec, 2);
	read(handle, &bsPointer->BPB_SecPerClus, 1);
	read(handle, &bsPointer->BPB_RsvdSecCnt, 2);
	read(handle, &bsPointer->BPB_NumFATs, 1);
	read(handle, &bsPointer->BPB_RootEntCnt, 2);
	read(handle, &bsPointer->BPB_TotSec16, 2);
	read(handle, &bsPointer->BPB_Media, 1);
	read(handle, &bsPointer->BPB_FATSz16, 2);
	read(handle, &bsPointer->BPB_SecPerTrk, 2);
	read(handle, &bsPointer->BPB_NumHeads, 2);
	read(handle, &bsPointer->BPB_HiddSec, 4);

	//read in and validate TotSec32
	read(handle, &bsPointer->BPB_TotSec32, 4);
	if(bsPointer->BPB_TotSec32 < 65525)
        {
        	printf("Inconsistent file system: BPB_TotSec32 must be >=65525  and value is %i\n", bsPointer->BPB_TotSec32);
        	exit(0);
        }

	//read in and validate FATSz32
	read(handle, &bsPointer->BPB_FATSz32, 4);
	if(bsPointer->BPB_FATSz32 == 0)        
	{
		printf("Inconsistent file system: BPB_FATSz32 must be non zero and value is %i\n", bsPointer->BPB_FATSz32);
		exit(0);
        }

	//continue reading other fields
	read(handle, &bsPointer->BPB_ExtFlags, 2);
	read(handle, &bsPointer->BPB_FSVerLow, 1);
	read(handle, &bsPointer->BPB_FSVerHigh, 1);

	//read in and validate RootClus
	read(handle, &bsPointer->BPB_RootClus, 4);
	if(bsPointer->BPB_RootClus < 2)
	{
		printf("Inconsistent file system: BPB_RootClus must be >=2  and value is %i\n", bsPointer->BPB_RootClus);           
               	exit(0);
        }

	//continue reading other fields
	read(handle, &bsPointer->BPB_FSInfo, 2);
	read(handle, &bsPointer->BPB_BkBootSec, 2);

	//read in BPB_reserved and validate all values are non-zero
	read(handle, &bsPointer->BPB_reserved, 12);
	for(int i = 0; i<12; i++)
	{
		if((unsigned char)bsPointer->BPB_reserved[i] != 0X00)
        	{
        		printf("Inconsistent file system: BPB_Reserved must be all 0s and value of BPB_reserved[%d] is %02X\n", i, (unsigned char)bsPointer->BPB_reserved[i]);
                	exit(0);
		}
	}

	//continue reading in other fields
	read(handle, &bsPointer->BS_DrvNum, 1);
	read(handle, &bsPointer->BS_Reserved1, 1);
	read(handle, &bsPointer->BS_BootSig, 1);
	read(handle, &bsPointer->BS_VolID, 4);
	read(handle, &bsPointer->BS_VolLab, 11);
	read(handle, &bsPointer->BS_FilSysType, 8);
	
	//if reading and validating the above fields does not crash program,
	//print success message
	printf("MBR appears to be consistent\n");
	
	//variable for fat entries
	uint32_t fatEntryX;

	//move to primary FAT in cluster 1
	lseek(handle, (bsPointer->BPB_RsvdSecCnt * bsPointer->BPB_BytesPerSec), SEEK_SET);
	
	//read in and validate FAT entry 0
	read(handle, &fatEntryX, 4);
	if(fatEntryX != 0x0FFFFFF8)
	{
		printf("Inconsistent file system: FAT[0] should be 0x0FFFFFF8 and value of FAT[0] is%02X\n", fatEntryX);
		exit(0);
	}

	//read in and validate FAT entry 1
	read(handle, &fatEntryX, 4);
        if((fatEntryX & 0x0FFFFFFF) != 0x0FFFFFFF)
        {
        	printf("Inconsistent file system: FAT[1] should be 0x0FFFFFFF and value of FAT[1] is    %02X\n", fatEntryX);
                exit(0);
        }

	lseek(handle, (bsPointer->BPB_RsvdSecCnt * bsPointer->BPB_BytesPerSec), SEEK_SET);
	
	//calculate the number of clusters to iterate through
	dataSec = bsPointer->BPB_TotSec32 - (bsPointer->BPB_RsvdSecCnt + (bsPointer->BPB_NumFATs * bsPointer->BPB_FATSz32));
	clusterCount = dataSec/bsPointer->BPB_SecPerClus;

	//iterate over FAT counting free clusters (all zero fat entries)
	for(uint32_t i = 0; i<clusterCount; i++)
	{
		read(handle, &fatEntryX, 4);
		if(fatEntryX == 0)
			freeCount++;
	}
 
	
	//move to start of cluster 0 and sector fsInfo to read in fsinfo fields
	int sectorSize = 512;
	lseek(handle, 0, SEEK_SET);	
	lseek(handle, bsPointer->BPB_FSInfo * sectorSize, SEEK_CUR);

	//read in LeadSig and validate it
	read(handle, &fsInfoPointer->FSI_LeadSig, 4);
	if(fsInfoPointer->FSI_LeadSig != 0x41615252)
	{
		printf("Inconsistent file system: FSI_LeadSig should be 0x41615252 and Value of FSI_LeadSig is %02X", fsInfoPointer->FSI_LeadSig);
		exit(0);
	}

	//read in 480 bytes of reserved1
	int arr_size = sizeof(fsInfoPointer->FSI_Reserved1)/sizeof(fsInfoPointer->FSI_Reserved1[0]);
	for(int i = 0; i<arr_size; i++)
	{
		read(handle, &fsInfoPointer->FSI_Reserved1[i], 1);
	}

	//read in StrucSig and validate it
	read(handle, &fsInfoPointer->FSI_StrucSig, 4);
	if(fsInfoPointer->FSI_StrucSig != 0x61417272)
	{
		printf("Inconsistent file system: FSI_StrucSig should be 0x61417272 and Value of FSI_StrucSig is %02X", fsInfoPointer->FSI_StrucSig);
		exit(0);
	}

	//read in FSI Free count field
	read(handle, &fsInfoPointer->FSI_Free_Count, 4);
}

//convert secNo sector to bytes
uint32_t sectorToBytes(uint32_t secNo)
{
	return secNo*bsPointer.BPB_BytesPerSec;
}

//convert clusterNo clusters to sectors
uint32_t clusterToSector(uint32_t clusterNo) {
    return ((clusterNo-2) * bsPointer.BPB_SecPerClus) + firstDataSector;
}

//convert clusterNo clusters to bytes
uint32_t clusterToBytes(uint32_t clusterNo)
{
	return clusterNo*bsPointer.BPB_SecPerClus*bsPointer.BPB_BytesPerSec;
}

//get directory name and remove invalid character
void extract_dir_name(uint8_t *dir, char *file_name) 
{
    int i;

    // Copy the filename
    for (i = 0; i < 11; i++) 
    {
        if (dir[i] == ' ') 
	{
            break;
        }
        file_name[i] = dir[i];
    }

    // Terminate the string
    file_name[i] = '\0';
}

//get file name and remove invalid character
void extract_file_name(uint8_t *dir, char *file_name)
{
    int i, j;

    // Copy the filename
    for (i = 0; i < 8; i++) 
    {
        if (dir[i] == ' ') 
	{
            break;
        }
        file_name[i] = dir[i];
    }

    // Copy the extension
    if (dir[8] != ' ') 
    {
        file_name[i++] = '.';
        for (j = 8; j < 11; j++) 
	{
            if (dir[j] == ' ') 
	    {
                break;
            }
            file_name[i++] = dir[j];
        }
    }

    // Terminate the string
    file_name[i] = '\0';
}

// given IMAGES/PANP.TXT or something similar, split into tokens of IMAGES and PANDP.TXT and store in array
void tokenizePath(const char* path, char** tokenArray, int* size) 
{
    char* temp_path = strdup(path); // make a copy of the original path so we can modify it
    if (temp_path == NULL) 
    {
        printf("Failed to allocate memory\n");
        return;
    }

    *size = 0;
    char* token = strtok(temp_path, "/");
    while (token != NULL) 
    {
        if (*size >= MAX_TOKEN_SIZE) 
	{
            printf("Path exceeds maximum depth\n");
            free(temp_path);
            return;
        }
        tokenArray[*size] = strdup(token);
        if (tokenArray[*size] == NULL)
	{
            printf("Failed to allocate memory\n");
            free(temp_path);
            return;
        }
        (*size)++;
        token = strtok(NULL, "/");
    }

    free(temp_path);
}

//function to write file found on volume to output file in local with same name
int readFileAndWrite(int handle, char *filename, uint32_t firstCluster, uint32_t fileSize) 
{
	int fd;
	char byte[1];

	//open a file named the same as the file we are searching the fat32 volume for
	if ((fd = open(filename, O_WRONLY|O_APPEND|O_CREAT, 0644)) < 0) 
	{
        	printf("Error: Failed to create output file\n");
        	return -1;
    	}
	
	//lseek to first cluster of file
    	off_t sector = clusterToSector(firstCluster);
    	if (lseek(handle, sectorToBytes(sector), SEEK_SET) == -1) 
	{
        	printf("Error: Failed to seek to file data\n");
        	close(fd);
        	return -1;
   	}

	//read the file and write byte by byte
    	for(uint32_t i=0; i<fileSize; i++)
    	{
		read(handle, &byte, 1);
		write(fd, byte, 1);
    	}

    	// Close the output file
    	close(fd);

    	return 0;
}

//traverse directories and print
void printDirectories(int handle, uint32_t clusterNo)
{
	//move to root directory
	uint32_t sector = clusterToSector(clusterNo);
    	lseek(handle, sectorToBytes(sector), SEEK_SET);

        //read directories in root directory, check if file or directory and if directory, enter it and repeat
	//a sector is 512 bytes but we are reading in chunks of 32 bytes wich is the size of a directory entry
    	for(uint32_t i = 0; i < (bsPointer.BPB_BytesPerSec/(sizeof(struct DirInfo))); i++) 
	{ 	
		//read fields of directory into directory Entry struct DirInfo and check values to determine action
		read(handle, &dirInfo, sizeof(struct DirInfo));

        	if ((unsigned char)(dirInfo.dir_name[0]) == 0x00) 
		{
            		// Entry is free, and there are no allocated directories after, so end traversing
            		break;
        	}

        	else if (((unsigned char)dirInfo.dir_name[0]) == 0xE5)
		{
            		// Entry is free, skip to next entry
            		continue;
        	}

		else if (((unsigned char)dirInfo.dir_name[0]) == 0x05)
		{
			//handle the special 0x05 value
        		dirInfo.dir_name[0] = 0xE5;
    		}

        	else if ((dirInfo.dir_attr) & (ATTR_LONG_NAME)) 
		{
            		// Entry is a long filename entry, skip it
	    		continue;
        	}

		else if(dirInfo.dir_attr & ATTR_HIDDEN)
        	{
			//Entry is hidden, skip it
            		continue;
        	}

		else if ((dirInfo.dir_name[0] == '.' & dirInfo.dir_name[1] == ' ') || (dirInfo.dir_name[0] == '.' & dirInfo.dir_name[1] == '.') ) 
		{
			//skip  . or .. entries
			continue;
    		}
		
        	else if ((dirInfo.dir_attr) == (ATTR_DIRECTORY)) 
		{
			// Entry is a subdirectory, recursively traverse it
            		char dirName[12];
            		extract_dir_name((uint8_t *)dirInfo.dir_name, dirName); //extract directory name, removing space paddings
			printf("Directory: %s\n", dirName);

			uint32_t myNextCluster = ((uint32_t)dirInfo.dir_first_cluster_hi)| dirInfo.dir_first_cluster_lo; //calculate offset to get contents of directory
	   
	        	if ((myNextCluster >= 2 && myNextCluster < EOC)) //make sure offset is within range (between root directory and EOC)
	        	{
	           		off_t currPos = lseek(handle, 0, SEEK_CUR); //save currentposition we are in the volume before entering the subdirectory
                   		printDirectories(handle, myNextCluster); //read subdirectory
	           		lseek(handle, currPos, SEEK_SET); //restore to position we wre at before entering the subdirectory
                	}
	    	}
	  	
        	else 
		{
        		// Entry is a file, extract and print its short name
           		char fileName[13]; //filename is of size 12 (8 chars for name, 1 char for '.', 3 chars for extension and 1 char for null pointer)
           		extract_file_name((uint8_t *)dirInfo.dir_name, fileName); //extract file name, adding cobining file with extension
	
			//get long name dir entry name and print its long name
			if(fileName[6] == '~') //file name we extracted indicates it has a long name
			{
				char val[32]; //store a long dir entry
				int level = 0;
				off_t currPos = lseek(handle, 0, SEEK_CUR); //save curr position before reading long entry
				char longFileName[MAX_LONG_FILE_NAME];
				int size = 0;

				do
				{
					lseek(handle, -(sizeof(struct DirInfo)*2), SEEK_CUR); //move to the directory entry before current directory entry (sizeof returns 32)
					read(handle, &val, 32); 
					level++; //we have gone up one directory before current
				}
				while(!((val[31] != '.') && (val[30] != '.') && (val[29] != '.') && (val[28] != '.'))); // while last 4 bytes of directory is not equal to '.' which indicates there are more long entries that hold name so keep looping
					
				lseek(handle, (sizeof(struct DirInfo)*(level-1)) - 32, SEEK_CUR); //go back down because the long file name is sotored from bottom to top
			 
				//read from bottom upwards to get name			
				for(int i=0; i<level; i++)
				{
					read(handle, &val, (sizeof(struct DirInfo))); //read 32 bytes
					
					//process 32 bytes and filer for characters not allowed in long file name
					for(int j = 1; j<32; j++) //check each position in val array
					{
						bool aToz = val[j] <= 90 && val[j] >= 64; //a to z
						bool AToZ = val[j] <= 122 && val[j] >= 94; //A to Z
						bool other3 = val[j] <= 41 && val[j] >= 36; //0 - 9
						bool other1 = val[j] <= 57 && val[j] >= 48; // rest of allowed characters
						bool other2 = val[j] == 45; // - char
     
						if((aToz) || (AToZ) || (other3) || (other1) || (other2)) //if not one of above, skip
						{
							longFileName[size] = val[j];
							size++;
						}
					}
					
					lseek(handle, -(sizeof(struct DirInfo)*2), SEEK_CUR); //move up
				}
				
				//put . before extension
				for(int i = size; i>size-3; i--)
				{ 
					longFileName[i] = longFileName[i-1]; //move over to right 	
				} 

				longFileName[size-3] = '.'; //put period to seperate extension
				longFileName[size+1] = '\0'; //terminate string name
				lseek(handle, currPos, SEEK_SET); //restore position we were at before we got long file name
				printf("File: %s  Long file name: %s\n", fileName, longFileName);
			}
			
			//print short file name
			else
			{
				 printf("File: %s\n", fileName);
			}
        	}

	}	

}

//read directories and sub directories to find file
void findAndReadFile(int handle, uint32_t clusterNo, char **tokenArray)
{
	//move to root directory
	uint32_t sector = clusterToSector(clusterNo);
    	lseek(handle, sectorToBytes(sector), SEEK_SET);

        //read directories in root directory, check if file or directory and if directory, enter it and repeat
	//a sector is 512 bytes but we are reading in chunks of 32 bytes wich is the size of a directory entry
    	for(uint32_t i = 0; i < (bsPointer.BPB_BytesPerSec/(sizeof(struct DirInfo))); i++) 
	{ 	
		//read fields of directory into directory Entry struct DirInfo and check values to determine action
		read(handle, &dirInfo, sizeof(struct DirInfo));

        	if ((unsigned char)(dirInfo.dir_name[0]) == 0x00) 
		{
            		// Entry is free, and there are no allocated directories after, so end traversing
            		break;
        	}

        	else if (((unsigned char)dirInfo.dir_name[0]) == 0xE5)
		{
            		// Entry is free, skip to next entry
            		continue;
        	}

		else if (((unsigned char)dirInfo.dir_name[0]) == 0x05)
		{
			//handle the special 0x05 value
        		dirInfo.dir_name[0] = 0xE5;
    		}

        	else if ((dirInfo.dir_attr) & (ATTR_LONG_NAME)) 
		{
            		// Entry is a long filename entry, skip it
	    		continue;
        	}

		else if(dirInfo.dir_attr & ATTR_HIDDEN)
        	{
			//Entry is hidden, skip it
            		continue;
        	}

		else if ((dirInfo.dir_name[0] == '.' & dirInfo.dir_name[1] == ' ') || (dirInfo.dir_name[0] == '.' & dirInfo.dir_name[1] == '.') ) 
		{
			//skip  . or .. entries
			continue;
    		}
		
        	else if ((dirInfo.dir_attr) == (ATTR_DIRECTORY)) 
		{
			// Entry is a subdirectory, recursively traverse it
            		char dirName[12];
            		extract_dir_name((uint8_t *)dirInfo.dir_name, dirName); //extract directory name, removing space paddings

			//if we found one of the directories in the path
	    		if(strcmp(dirName,tokenArray[arrIndex]) == 0) 
	    		{
				printf("found directory %s, entering it\n", dirName);
					
	        		uint32_t myNextCluster = ((uint32_t)dirInfo.dir_first_cluster_hi)| dirInfo.dir_first_cluster_lo; //calculate offset to get contents of directory
	   
	        		if ((myNextCluster >= 2 && myNextCluster < EOC)) //make sure offset is within range (between root directory and EOC)
	        		{
	           			off_t currPos = lseek(handle, 0, SEEK_CUR); //save currentposition we are in the volume before entering the subdirectory
	           			arrIndex++;
                   			findAndReadFile(handle, myNextCluster, tokenArray); //read subdirectory
	           			lseek(handle, currPos, SEEK_SET); //restore to position we wre at before entering the subdirectory
                		}
	    		}
	  	
        	}

        	else 
		{
        		// Entry is a file, extract and print its name
           		char fileName[13];
           		extract_file_name((uint8_t *)dirInfo.dir_name, fileName); //extract file name, adding cobining file with extension

			//if we found the file
	   		if(strcmp(fileName, tokenArray[tokArrSize-1]) == 0)
	   		{	
				foundFile = true;
           			printf("found file : %s\n", fileName);
				uint32_t firstCluster = ((uint32_t)dirInfo.dir_first_cluster_hi) | dirInfo.dir_first_cluster_lo; //calculate offset to get contents of file
				readFileAndWrite(handle, fileName, firstCluster, dirInfo.dir_file_size); //write file to another file
				printf("Contents of %s has been written into a file named %s\n ", fileName, fileName);
	   		}
        	}

	}
   
}
